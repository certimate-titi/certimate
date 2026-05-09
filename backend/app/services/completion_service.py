"""CompletionService — 科目完成度框架計算服務.

對應 orphan-mitigation-design.md B.2 進度條算法 / B.3 徽章里程碑 / B.4 邊際效益遞減。

算法摘要：
    S = Σ(w_i × m_i_adjusted) / Σ(w_i)

    w_i = 出題頻率權重 × 深度層級權重
    m_i_adjusted = m_i × 0.6（若來自 AI_INFERRED 鷹架）else m_i

    分母選擇：
        sweet_spot  — 僅含出題頻率 ≥ 1 次節點
        full_coverage — 所有 depth=2 節點
        sprint_mode — 前 30% 高頻節點
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.learning_journey import LearningJourney
from app.services.base import BaseService


# ── 出題頻率權重 ──────────────────────────────────────────────────────────
def _exam_freq_weight(freq: int) -> float:
    """考古題命中次數 → 出題頻率權重。"""
    if freq >= 5:
        return 3.0
    if freq >= 2:
        return 2.0
    if freq >= 1:
        return 1.5
    return 1.0


# ── 深度層級權重 ──────────────────────────────────────────────────────────
def _depth_weight(depth: int) -> float:
    """知識節點樹深度 → 深度層級權重。"""
    if depth == 1:
        return 0.5
    if depth == 3:
        return 1.2
    return 1.0  # depth == 2 (主力)


# ── 節點 mastery 值（B.2.1 定義） ──────────────────────────────────────────
def _mastery_value(nm: Optional[NodeMastery]) -> float:
    """依 NodeMastery SM-2 狀態轉換 0/0.5/1.0/1.5。

    - 無紀錄 / UNSEEN → 0.0
    - 答題正確率 < 60% → 0.5
    - 正確率 ≥ 60% + SM-2 間隔 ≥ 4 天 → 1.0
    - 正確率 ≥ 85% + SM-2 間隔 ≥ 14 天 → 1.5

    用 base_mastery 作為正確率代理（0.0~1.0），
    last_tested_at + next_review_at 推算 SM-2 間隔。
    """
    if nm is None:
        return 0.0

    rate = float(nm.base_mastery or 0.0)
    interval_days = _sm2_interval(nm)

    if rate >= 0.85 and interval_days >= 14:
        return 1.5
    if rate >= 0.60 and interval_days >= 4:
        return 1.0
    if nm.total_count > 0:
        return 0.5
    return 0.0


def _sm2_interval(nm: NodeMastery) -> int:
    """推算 SM-2 間隔天數（next_review_at - last_tested_at）。"""
    if nm.last_tested_at is None or nm.next_review_at is None:
        return 0
    delta = nm.next_review_at - nm.last_tested_at
    return max(0, delta.days)


# ── 是否為 AI_INFERRED 鷹架 ───────────────────────────────────────────────
def _is_ai_inferred(nm: Optional[NodeMastery]) -> bool:
    """判斷 mastery 是否來自 AI_INFERRED 鷹架（信任等級）。

    NodeMastery 本身無 trust_level；此判斷依 status 欄位約定：
    scaffold pipeline 在 AI 補洞後將 status 設為 'AI_INFERRED'。
    """
    if nm is None:
        return False
    return (nm.status or "").upper() == "AI_INFERRED"


# ── 徽章判定 ─────────────────────────────────────────────────────────────
_BADGE_ORDER = [
    ("starter",              lambda ss, fc, hs: hs),
    ("explorer",             lambda ss, fc, hs: ss >= 25),
    ("builder",              lambda ss, fc, hs: ss >= 50),
    ("sweet_spot_achiever",  lambda ss, fc, hs: ss >= 85),
    ("frequent_master",      lambda ss, fc, hs: ss >= 100),
    ("full_coverage_master", lambda ss, fc, hs: fc >= 100),
]


def _check_badges(
    sweet_spot: float, full_coverage: float, has_started: bool
) -> list[str]:
    """判定已解鎖的徽章清單（依條件順序）。"""
    unlocked = []
    for code, cond in _BADGE_ORDER:
        if cond(sweet_spot, full_coverage, has_started):
            unlocked.append(code)
    return unlocked


# ── 下一個未解鎖里程碑 ────────────────────────────────────────────────────
def _next_milestone(
    sweet_spot: float, full_coverage: float, has_started: bool
) -> Optional[dict]:
    """找出最近未解鎖的徽章及距離百分比。"""
    thresholds = [
        ("starter", None),         # 以 has_started 判定，非數值門檻
        ("explorer", 25.0),
        ("builder", 50.0),
        ("sweet_spot_achiever", 85.0),
        ("frequent_master", 100.0),
        ("full_coverage_master", None),  # 依 full_coverage
    ]
    if not has_started:
        return {"code": "starter", "remaining_pct": None}

    for code, threshold in thresholds[1:]:  # skip starter（已 has_started）
        if code == "full_coverage_master":
            if full_coverage < 100:
                return {"code": code, "remaining_pct": round(100 - full_coverage, 1)}
        elif sweet_spot < threshold:
            return {"code": code, "remaining_pct": round(threshold - sweet_spot, 1)}
    return None  # 全部解鎖


# ── 邊際效益遞減 nudge（B.4.1）─────────────────────────────────────────────
def _check_marginal_nudge(
    sweet_spot: float,
    days_to_exam: Optional[int],
    full_coverage: float,
) -> bool:
    """B.4.1 觸發條件（AND 關係）：
    1. sweet_spot ≥ 85%
    2. 距考試 ≤ 14 天（exam_date 已填）
    3. full_coverage < 100%
    """
    if sweet_spot < 85:
        return False
    if days_to_exam is None or days_to_exam > 14:
        return False
    if full_coverage >= 100:
        return False
    return True


def _days_to_exam(journey: Optional[LearningJourney]) -> Optional[int]:
    """計算距考試日天數（today 起算，含 0）。"""
    if journey is None or journey.exam_date is None:
        return None
    today = date.today()
    delta = journey.exam_date - today
    return delta.days


class CompletionService(BaseService):
    """科目完成度框架計算服務。

    對外暴露 compute() 方法；內部使用純函式完成加權計算。
    """

    def compute(self, user_id: str, subject_id: str) -> dict:
        """計算指定用戶在指定科目的完成度，回傳完整 payload。

        Args:
            user_id: 用戶 UUID 字串
            subject_id: 科目 UUID 字串

        Returns:
            {
                subject_id, sweet_spot_progress, full_coverage_progress,
                sprint_mode_progress, badges_unlocked, next_milestone,
                should_show_marginal_utility_nudge, computed_at
            }

        Raises（透過 error dict）:
            404 — 科目不存在
            403 — （預留；本版本以科目存在性為主要守衛）
        """
        # ── 解析 UUID ──────────────────────────────────────────────────
        try:
            sid = uuid.UUID(subject_id)
            uid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            return self.error("無效的 ID 格式", 400)

        # ── 科目驗證 ────────────────────────────────────────────────────
        subject = self.db.query(Subject).filter_by(id=sid).first()
        if subject is None:
            return self.error("科目不存在", 404)

        # ── 取得該科目所有節點 ──────────────────────────────────────────
        nodes = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.subject_id == sid)
            .all()
        )

        # ── 取得用戶所有 NodeMastery（此科目節點） ─────────────────────
        node_ids = [n.id for n in nodes]
        mastery_map: dict[uuid.UUID, NodeMastery] = {}
        if node_ids:
            for nm in (
                self.db.query(NodeMastery)
                .filter(
                    NodeMastery.user_id == uid,
                    NodeMastery.node_id.in_(node_ids),
                )
                .all()
            ):
                mastery_map[nm.node_id] = nm

        # ── 取得學習旅程（用於 nudge 判定） ────────────────────────────
        journey = (
            self.db.query(LearningJourney)
            .filter_by(user_id=uid, subject_id=sid)
            .first()
        )
        days = _days_to_exam(journey)

        # ── 計算三種進度 ─────────────────────────────────────────────────
        sweet_spot = self._calc_sweet_spot(nodes, mastery_map)
        full_coverage = self._calc_full_coverage(nodes, mastery_map)
        sprint_mode = self._calc_sprint_mode(nodes, mastery_map)

        # ── 徽章判定 ─────────────────────────────────────────────────────
        has_started = any(
            _mastery_value(nm) > 0 for nm in mastery_map.values()
        )
        badges = _check_badges(sweet_spot, full_coverage, has_started)
        next_ms = _next_milestone(sweet_spot, full_coverage, has_started)
        nudge = _check_marginal_nudge(sweet_spot, days, full_coverage)

        return {
            "ok": True,
            "subject_id": str(sid),
            "sweet_spot_progress": round(sweet_spot),
            "full_coverage_progress": round(full_coverage),
            "sprint_mode_progress": round(sprint_mode),
            "badges_unlocked": badges,
            "next_milestone": next_ms,
            "should_show_marginal_utility_nudge": nudge,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── 三種分母計算 ────────────────────────────────────────────────────

    def _calc_sweet_spot(
        self,
        nodes: list[KnowledgeNode],
        mastery_map: dict[uuid.UUID, NodeMastery],
    ) -> float:
        """sweet_spot：分母僅含出題頻率 ≥ 1 次節點。"""
        eligible = [n for n in nodes if (n.available_questions or 0) >= 1]
        return self._weighted_score(eligible, mastery_map)

    def _calc_full_coverage(
        self,
        nodes: list[KnowledgeNode],
        mastery_map: dict[uuid.UUID, NodeMastery],
    ) -> float:
        """full_coverage：分母含所有 depth=2 節點。"""
        d2 = [n for n in nodes if n.depth == 2]
        return self._weighted_score(d2, mastery_map)

    def _calc_sprint_mode(
        self,
        nodes: list[KnowledgeNode],
        mastery_map: dict[uuid.UUID, NodeMastery],
    ) -> float:
        """sprint_mode：前 30% 高頻節點（依 available_questions 降冪）。"""
        freq_nodes = sorted(
            [n for n in nodes if (n.available_questions or 0) >= 1],
            key=lambda n: n.available_questions or 0,
            reverse=True,
        )
        top30_count = max(1, round(len(freq_nodes) * 0.3))
        top_nodes = freq_nodes[:top30_count]
        return self._weighted_score(top_nodes, mastery_map)

    def _node_weight(self, node: KnowledgeNode) -> float:
        """計算節點總權重 w_i = 出題頻率權重 × 深度層級權重。"""
        freq = node.available_questions or 0
        return _exam_freq_weight(freq) * _depth_weight(node.depth)

    def _weighted_score(
        self,
        nodes: list[KnowledgeNode],
        mastery_map: dict[uuid.UUID, NodeMastery],
    ) -> float:
        """加權分數 S = Σ(w_i × m_i_adjusted) / Σ(w_i)，回傳 0-100。"""
        if not nodes:
            return 0.0

        total_w = 0.0
        weighted_m = 0.0

        for node in nodes:
            w = self._node_weight(node)
            nm = mastery_map.get(node.id)
            m = _mastery_value(nm)

            # AI_INFERRED 降權 0.6
            if _is_ai_inferred(nm):
                m = m * 0.6

            # mastery 最大值為 1.5，正規化到 0-1 後算百分比
            total_w += w
            weighted_m += w * m

        if total_w == 0:
            return 0.0

        # m 最大值 1.5 → 正規化分母 × 1.5 to get 0-100%
        raw = weighted_m / (total_w * 1.5)
        return min(100.0, raw * 100.0)
