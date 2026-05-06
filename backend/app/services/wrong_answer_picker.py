"""WrongAnswerPicker — 錯題考試智能挑題（4 階段時程感知 + 多桶配額）。

設計原則：
1. 多桶配額避免舊錯題壟斷（不同階段配比不同）
2. 桶不足時往下一桶補
3. 桶內隨機選題，避免每次相同
4. 「消除規則」：連續答對 ≥ 2 次 OR user_marked_mastered = TRUE → 不再挑
5. 受 plan_limit 與用戶選的題數限制
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any
import random
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.answer import Answer
from app.models.question import Question
from app.models.exam import Exam
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.subject import Subject
from app.models.learning_journey import LearningJourney


# 4 階段桶配比（百分比加總 = 100）
PHASE_RATIOS: dict[str, dict[str, int]] = {
    "mastery":  {"overdue": 25, "fresh": 45, "weak": 20, "random": 10},
    "standard": {"overdue": 40, "fresh": 30, "weak": 20, "random": 10},
    "sprint":   {"overdue": 60, "fresh": 15, "weak": 20, "random": 5},
    "final":    {"overdue": 70, "fresh": 10, "weak": 20, "random": 0},
}


def _calculate_phase(exam_date: date | None, today: date) -> str:
    """4 階段時程推導（與 schedule_service._calculate_mode 對齊）。"""
    if not exam_date:
        return "standard"
    days = (exam_date - today).days
    if days <= 7:
        return "final"
    if days <= 30:
        return "sprint"
    if days <= 180:
        return "standard"
    return "mastery"


class WrongAnswerPicker:
    """錯題挑題服務。"""

    def __init__(self, db: Session):
        self.db = db

    def pick(
        self,
        user_id: uuid.UUID,
        subject_id: uuid.UUID | None,
        target_count: int,
    ) -> dict[str, Any]:
        """智能挑題主流程。

        Args:
            user_id: 使用者 ID
            subject_id: 科目（None 表跨科目）
            target_count: 用戶想要的題數（受 plan_limit 與候選池上限）

        Returns:
            {
                "questions": [{question_id, ...}],
                "phase": "sprint",
                "phase_reason": "距考 25 天",
                "buckets": {"overdue": N, "fresh": N, "weak": N, "random": N},
                "total_candidates": int,
            }
        """
        today = datetime.now(timezone.utc).date()

        # 階段推導
        exam_date = None
        if subject_id:
            j = self.db.query(LearningJourney).filter_by(
                user_id=user_id, subject_id=subject_id
            ).first()
            if j and j.exam_date:
                exam_date = j.exam_date
        phase = _calculate_phase(exam_date, today)
        days_left = (exam_date - today).days if exam_date else None
        phase_reason = (
            f"距考 {days_left} 天 → {phase} 模式" if days_left is not None
            else f"無考試日 → 預設 {phase}"
        )

        # 蒐集候選錯題（過濾已消除）
        candidates = self._collect_candidates(user_id, subject_id, today)
        if not candidates:
            return {
                "questions": [],
                "phase": phase,
                "phase_reason": phase_reason,
                "buckets": {"overdue": 0, "fresh": 0, "weak": 0, "random": 0},
                "total_candidates": 0,
                "message": "目前無錯題可考",
            }

        # 桶分類
        buckets = self._classify_to_buckets(candidates, today)

        # 依配比挑題
        ratios = PHASE_RATIOS[phase]
        picked_ids: list[uuid.UUID] = []
        bucket_counts: dict[str, int] = {}

        # 計算每桶目標題數（餘額流動）
        remaining = target_count
        for bucket_name in ("overdue", "fresh", "weak", "random"):
            quota = round(target_count * ratios[bucket_name] / 100)
            quota = min(quota, len(buckets[bucket_name]), remaining)
            if quota > 0:
                # 桶內隨機 sample
                pool = [c for c in buckets[bucket_name] if c["question_id"] not in picked_ids]
                sampled = random.sample(pool, min(quota, len(pool)))
                for s in sampled:
                    picked_ids.append(s["question_id"])
                bucket_counts[bucket_name] = len(sampled)
                remaining -= len(sampled)
            else:
                bucket_counts[bucket_name] = 0

        # 桶不足時：從未取過的全部候選池補足
        if remaining > 0:
            leftover = [c for c in candidates if c["question_id"] not in picked_ids]
            extra = random.sample(leftover, min(remaining, len(leftover)))
            for e in extra:
                picked_ids.append(e["question_id"])
            bucket_counts["overflow"] = len(extra)

        return {
            "questions": [{"question_id": str(qid)} for qid in picked_ids],
            "phase": phase,
            "phase_reason": phase_reason,
            "buckets": bucket_counts,
            "total_candidates": len(candidates),
        }

    def _collect_candidates(
        self,
        user_id: uuid.UUID,
        subject_id: uuid.UUID | None,
        today: date,
    ) -> list[dict[str, Any]]:
        """蒐集候選錯題：is_correct=FALSE 且未消除（streak < 2 且未手動標記掌握）。"""
        # 預載手動標記掌握的題目集
        from app.models.user_question_override import UserQuestionOverride
        mastered_qids = {
            r[0] for r in self.db.query(UserQuestionOverride.question_id)
            .filter(UserQuestionOverride.user_id == user_id, UserQuestionOverride.is_mastered == True)  # noqa: E712
            .all()
        }
        # 取每個 question 的最新 answer
        latest = (
            self.db.query(
                Answer.question_id,
                func.max(Answer.answered_at).label("latest_at"),
            )
            .filter(Answer.user_id == user_id)
            .group_by(Answer.question_id)
            .subquery()
        )

        # 加入該 question 的 streak（連續答對次數）
        # 簡化：直接看最新一次是否答錯
        q = (
            self.db.query(
                Answer.question_id,
                Answer.is_correct,
                Answer.answered_at,
                Answer.confidence,
            )
            .join(latest, and_(
                Answer.question_id == latest.c.question_id,
                Answer.answered_at == latest.c.latest_at,
            ))
            .filter(Answer.user_id == user_id)
            .filter(Answer.is_correct == False)  # noqa: E712
        )

        if subject_id:
            q = q.join(Question, Question.id == Answer.question_id).filter(
                Question.subject_id == subject_id
            )

        rows = q.all()
        candidates = []
        for r in rows:
            qid = r[0]
            answered_at = r[2]
            # 手動標記掌握的題目跳過
            if qid in mastered_qids:
                continue
            # 計算這題的 correct_streak（從最新一次往前數連續答對）
            streak = self._compute_correct_streak(user_id, qid)
            if streak >= 2:
                continue  # 自動消除
            candidates.append({
                "question_id": qid,
                "answered_at": answered_at,
                "streak": streak,
            })
        return candidates

    def _compute_correct_streak(self, user_id: uuid.UUID, question_id: uuid.UUID) -> int:
        """計算該題從最新往前的連續答對次數（最新一次答錯則 streak = 0）。"""
        rows = (
            self.db.query(Answer.is_correct)
            .filter(Answer.user_id == user_id, Answer.question_id == question_id)
            .order_by(Answer.answered_at.desc())
            .all()
        )
        streak = 0
        for r in rows:
            if r[0]:
                streak += 1
            else:
                break
        return streak

    def _classify_to_buckets(
        self,
        candidates: list[dict],
        today: date,
    ) -> dict[str, list[dict]]:
        """把候選錯題分到 4 個桶。

        - overdue: 答錯後超過 3 天未複習
        - fresh: 近 7 天內的新錯題
        - weak: 該題對應節點的 mastery_rate < 60%
        - random: 其他
        """
        buckets: dict[str, list[dict]] = {
            "overdue": [], "fresh": [], "weak": [], "random": [],
        }

        # 預先撈所有 questions 的 node mastery
        qids = [c["question_id"] for c in candidates]
        mastery_map: dict[uuid.UUID, int] = {}
        if qids:
            node_rows = (
                self.db.query(Question.id, NodeMastery.mastery_rate)
                .join(NodeMastery, NodeMastery.node_id == Question.node_id, isouter=True)
                .filter(Question.id.in_(qids))
                .all()
            )
            for qid, m in node_rows:
                mastery_map[qid] = int(m or 0)

        for c in candidates:
            answered_at = c["answered_at"]
            answered_date = answered_at.date() if hasattr(answered_at, "date") else answered_at
            days_since = (today - answered_date).days
            mastery = mastery_map.get(c["question_id"], 0)

            if days_since > 3:
                buckets["overdue"].append(c)
            elif days_since <= 7:
                buckets["fresh"].append(c)
            elif mastery < 60:
                buckets["weak"].append(c)
            else:
                buckets["random"].append(c)
        return buckets
