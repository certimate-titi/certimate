"""SM-2 State Machine Engine — 動態知識庫核心演算法.

SuperMemo 2 演算法的 TiTi 版本，支援：
- 考試結果驅動的 base_mastery 更新
- ease_factor 自適應調整（控制衰退速度）
- Read-time 記憶保留率計算（指數衰退）
- 狀態轉換：UNSEEN → CRITICAL / PENDING / MASTERED

使用方式：
    engine = SM2Engine()

    # 處理考試答案
    state = engine.process_exam_answers(user_id, topic_states, exam_answers)

    # 計算有效進度（API 回傳時呼叫）
    effective = engine.calculate_effective_progress(state, now)
"""

import math
from datetime import datetime, timedelta, timezone
from typing import NamedTuple


class TopicState(NamedTuple):
    """節點狀態快照。"""
    base_mastery: float      # 0.0 ~ 1.0
    ease_factor: float       # >= 1.3
    last_tested_at: datetime | None
    next_review_at: datetime | None
    status: str              # UNSEEN / CRITICAL / PENDING / MASTERED


class SM2Engine:
    """SuperMemo 2 狀態機 — 考試結果驅動掌握度更新。"""

    # ── 常數 ────────────────────────────────────────────────────
    MIN_EASE_FACTOR = 1.3
    DEFAULT_EASE_FACTOR = 2.5
    RETENTION_FLOOR = 0.7      # 衰退下限（避免過度恐慌）
    DEFAULT_REVIEW_DAYS = 14   # 預設複習間隔

    # SM-2 quality → 分數映射
    # quality 0-2: 失敗, 3: 勉強, 4: 正確, 5: 輕鬆
    QUALITY_CORRECT = 4
    QUALITY_EASY = 5
    QUALITY_BARELY = 3
    QUALITY_WRONG = 1

    # ── 單題處理 ────────────────────────────────────────────────

    def process_answer(
        self,
        state: TopicState,
        is_correct: bool,
        quality: int | None = None,
        now: datetime | None = None,
    ) -> TopicState:
        """處理單題答案，回傳更新後的狀態。

        Args:
            state: 當前節點狀態
            is_correct: 是否答對
            quality: SM-2 品質分數 (0-5)，None 時自動推算
            now: 當前時間
        """
        now = now or datetime.now(timezone.utc)

        if quality is None:
            quality = self.QUALITY_CORRECT if is_correct else self.QUALITY_WRONG

        # 更新 ease_factor（SM-2 公式）
        ef = state.ease_factor
        ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ef = max(self.MIN_EASE_FACTOR, ef)

        # 更新 base_mastery（指數加權移動平均）
        alpha = 0.3  # 學習率
        answer_score = 1.0 if is_correct else 0.0
        new_mastery = state.base_mastery * (1 - alpha) + answer_score * alpha

        # 計算下次複習間隔
        if is_correct:
            if state.status == "UNSEEN":
                interval_days = 1
            elif state.status == "CRITICAL":
                interval_days = 3
            else:
                interval_days = max(1, int(self.DEFAULT_REVIEW_DAYS * ef / self.DEFAULT_EASE_FACTOR))
        else:
            interval_days = 1  # 答錯 → 明天就要複習

        next_review = now + timedelta(days=interval_days)

        # 狀態轉換
        if new_mastery >= 0.7:
            new_status = "MASTERED"
        elif new_mastery >= 0.4:
            new_status = "PENDING"
        elif new_mastery > 0:
            new_status = "CRITICAL"
        else:
            new_status = "UNSEEN"

        return TopicState(
            base_mastery=round(new_mastery, 4),
            ease_factor=round(ef, 4),
            last_tested_at=now,
            next_review_at=next_review,
            status=new_status,
        )

    # ── 批次處理（考試結算）──────────────────────────────────────

    def process_exam_answers(
        self,
        topic_answers: dict[str, list[bool]],
        topic_states: dict[str, TopicState],
        now: datetime | None = None,
    ) -> dict[str, TopicState]:
        """批次處理一場考試的所有答案。

        Args:
            topic_answers: {topic_id: [is_correct, ...]} 按題目分組的答案
            topic_states: {topic_id: TopicState} 考前的節點狀態
            now: 當前時間

        Returns:
            {topic_id: TopicState} 更新後的狀態
        """
        now = now or datetime.now(timezone.utc)
        results = {}

        for topic_id, answers in topic_answers.items():
            state = topic_states.get(topic_id, TopicState(
                base_mastery=0.0,
                ease_factor=self.DEFAULT_EASE_FACTOR,
                last_tested_at=None,
                next_review_at=None,
                status="UNSEEN",
            ))

            # 依序處理每題（保持時序）
            for is_correct in answers:
                state = self.process_answer(state, is_correct, now=now)

            results[topic_id] = state

        return results

    # ── Read-time 衰退計算 ──────────────────────────────────────

    def calculate_retention(
        self,
        state: TopicState,
        now: datetime | None = None,
    ) -> float:
        """計算當前記憶保留率（0.0 ~ 1.0）。

        公式：
            if now <= next_review_at: return 1.0（記憶尚新鮮）
            if decayed: return max(FLOOR, e^(-λ * elapsed_hours))
        """
        now = now or datetime.now(timezone.utc)

        if state.status == "UNSEEN":
            return 0.0

        if state.next_review_at is None or state.last_tested_at is None:
            return 1.0

        if now <= state.next_review_at:
            return 1.0  # 記憶尚新鮮

        # 衰退計算
        elapsed = (now - state.next_review_at).total_seconds() / 3600  # 小時
        lambda_decay = 0.05 / max(1.0, state.ease_factor)  # ease_factor 越高衰退越慢
        retention = math.exp(-lambda_decay * elapsed)

        return max(self.RETENTION_FLOOR, round(retention, 4))

    def calculate_effective_progress(
        self,
        state: TopicState,
        now: datetime | None = None,
    ) -> float:
        """計算有效進度 = base_mastery × retention。"""
        retention = self.calculate_retention(state, now)
        return round(state.base_mastery * retention, 4)

    def get_decay_status(
        self,
        state: TopicState,
        now: datetime | None = None,
    ) -> str:
        """判斷衰退狀態。"""
        now = now or datetime.now(timezone.utc)

        if state.status == "UNSEEN":
            return "unseen"

        if state.next_review_at is None:
            return "fresh"

        if now <= state.next_review_at:
            return "fresh"

        retention = self.calculate_retention(state, now)
        if retention >= 0.9:
            return "fresh"
        elif retention >= 0.8:
            return "decaying"
        else:
            return "critical"

    # ── Refresh Quiz 結算 ───────────────────────────────────────

    def process_refresh_quiz(
        self,
        state: TopicState,
        all_correct: bool,
        now: datetime | None = None,
    ) -> TopicState:
        """處理記憶喚醒小測驗結果。

        全部答對 → next_review_at 延長，effective progress 恢復
        有錯 → 標記為 CRITICAL，縮短複習間隔
        """
        now = now or datetime.now(timezone.utc)

        if all_correct:
            # 喚醒成功：延長複習間隔
            interval_days = max(7, int(self.DEFAULT_REVIEW_DAYS * state.ease_factor / 2))
            return TopicState(
                base_mastery=state.base_mastery,
                ease_factor=min(state.ease_factor + 0.1, 3.0),
                last_tested_at=now,
                next_review_at=now + timedelta(days=interval_days),
                status="MASTERED" if state.base_mastery >= 0.7 else "PENDING",
            )
        else:
            # 喚醒失敗：縮短間隔
            return TopicState(
                base_mastery=state.base_mastery,
                ease_factor=max(self.MIN_EASE_FACTOR, state.ease_factor - 0.2),
                last_tested_at=now,
                next_review_at=now + timedelta(days=1),
                status="CRITICAL",
            )
