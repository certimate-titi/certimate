"""ShareBadgeService — 考試結束後的分享徽章資料產生器（不含絕對分數）。

設計原則：
1. 永遠正向 — 即便首考、低分、退步，都能找到正向敘事
2. 學習風格徽章是「身份標籤」非「能力評等」，分享出去無壓力
3. 用累積里程取代瞬時表現
"""

from datetime import datetime, timezone, timedelta
from typing import Any
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.exam import Exam
from app.models.answer import Answer
from app.models.question import Question
from app.models.subject import Subject
from app.models.user import User


# 7 種學習風格（依答題行為自動分型）
_STYLE_DEFS = {
    "tactical": {
        "label": "戰術型考生",
        "emoji": "🎯",
        "description": "擅長從錯題建立系統化思維",
    },
    "socratic": {
        "label": "蘇格拉底愛好者",
        "emoji": "💭",
        "description": "勤於追問、深度思辨",
    },
    "sprint": {
        "label": "衝刺型考生",
        "emoji": "🚀",
        "description": "短時間爆發力強，集中火力突破",
    },
    "marathon": {
        "label": "馬拉松型考生",
        "emoji": "🏃",
        "description": "長期穩定累積，水滴石穿",
    },
    "steady": {
        "label": "穩紮穩打型",
        "emoji": "🌳",
        "description": "答題正確率漸進向上，根基扎實",
    },
    "reflective": {
        "label": "反思型考生",
        "emoji": "🪞",
        "description": "每題都校準信心度，自我覺察強",
    },
    "explorer": {
        "label": "成長型考生",
        "emoji": "✨",
        "description": "正在踏上備考之路，每一步都算數",
    },
}


class ShareBadgeService:
    """產生分享徽章資料。"""

    def __init__(self, db: Session):
        self.db = db

    def build_badge(self, exam_id: str, user_id: str) -> dict[str, Any]:
        try:
            exam_uuid = uuid.UUID(exam_id)
            user_uuid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            return {"error": True, "status_code": 400, "message": "ID 格式錯誤"}

        exam = self.db.query(Exam).filter_by(id=exam_uuid, user_id=user_uuid).first()
        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}

        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        subject_name = ""
        if exam.subject_id:
            s = self.db.query(Subject).filter_by(id=exam.subject_id).first()
            if s:
                subject_name = s.name or ""

        return {
            "ok": True,
            "exam_id": str(exam.id),
            "exam_meta": {
                "subject_name": subject_name,
                "title": exam.title or "模擬測驗",
                "completed_at": (exam.completed_at or exam.created_at).isoformat() if (exam.completed_at or exam.created_at) else None,
            },
            "user": {
                "display_name": user.display_name or (user.email.split("@")[0] if user.email else "考生"),
            },
            "improvement": self._calc_improvement(exam, user_uuid),
            "cumulative": self._calc_cumulative(user_uuid, exam),
            "learning_style": self._classify_learning_style(user_uuid),
        }

    # ─── A：進步幅度 ─────────────────────────────────────────────────

    def _calc_improvement(self, current_exam: Exam, user_uuid: uuid.UUID) -> dict:
        """與同 subject 上一次測驗比較答對率（百分點）。

        若無上次測驗 → 回傳「首次完成」訊息（仍正向）。
        """
        cur_correct, cur_total = self._exam_accuracy(current_exam.id, user_uuid)
        cur_pct = round((cur_correct / cur_total * 100) if cur_total > 0 else 0)

        if not current_exam.subject_id:
            return {"is_first": True, "message": "完成一份測驗 ✨", "delta_pp": 0}

        prev = (
            self.db.query(Exam)
            .filter(
                Exam.user_id == user_uuid,
                Exam.subject_id == current_exam.subject_id,
                Exam.id != current_exam.id,
                Exam.completed_at.isnot(None),
            )
            .order_by(Exam.completed_at.desc())
            .first()
        )
        if not prev:
            return {"is_first": True, "message": "首次完成此科目測驗 🎉", "delta_pp": 0}

        prev_correct, prev_total = self._exam_accuracy(prev.id, user_uuid)
        prev_pct = round((prev_correct / prev_total * 100) if prev_total > 0 else 0)
        delta = cur_pct - prev_pct

        if delta > 0:
            return {"is_first": False, "message": f"比上次提升 {delta} 個百分點", "delta_pp": delta}
        if delta == 0:
            return {"is_first": False, "message": "持續穩定發揮 💪", "delta_pp": 0}
        return {"is_first": False, "message": f"已累積 {self._exam_count(user_uuid)} 份測驗經驗", "delta_pp": delta}

    def _exam_accuracy(self, exam_id: uuid.UUID, user_uuid: uuid.UUID) -> tuple[int, int]:
        """回傳（正確題數, 總題數）。"""
        rows = (
            self.db.query(Answer.is_correct)
            .filter(Answer.user_id == user_uuid, Answer.exam_id == exam_id)
            .all()
        )
        if not rows:
            return 0, 0
        return sum(1 for r in rows if r[0]), len(rows)

    # ─── B：累積里程 ─────────────────────────────────────────────────

    def _calc_cumulative(self, user_uuid: uuid.UUID, current_exam: Exam) -> dict:
        total_exams = self._exam_count(user_uuid)
        total_questions = (
            self.db.query(func.count(Answer.id))
            .filter(Answer.user_id == user_uuid)
            .scalar()
            or 0
        )
        streak_days = self._consecutive_active_days(user_uuid)
        return {
            "total_exams": int(total_exams),
            "total_questions": int(total_questions),
            "streak_days": int(streak_days),
        }

    def _exam_count(self, user_uuid: uuid.UUID) -> int:
        return (
            self.db.query(func.count(Exam.id))
            .filter(Exam.user_id == user_uuid, Exam.completed_at.isnot(None))
            .scalar()
            or 0
        )

    def _consecutive_active_days(self, user_uuid: uuid.UUID) -> int:
        """連續答題天數（往回掃 30 天，遇到斷層停止）。"""
        today = datetime.now(timezone.utc).date()
        days = (
            self.db.query(func.date(Answer.answered_at))
            .filter(Answer.user_id == user_uuid)
            .filter(Answer.answered_at >= datetime.now(timezone.utc) - timedelta(days=30))
            .distinct()
            .all()
        )
        active_dates = {row[0] for row in days if row[0]}
        streak = 0
        cursor = today
        while cursor in active_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    # ─── D：學習風格分型 ─────────────────────────────────────────────

    def _classify_learning_style(self, user_uuid: uuid.UUID) -> dict:
        """以最簡單的規則分型，回傳對應風格 dict。

        規則優先順序（命中第一個即停）：
        1. 蘇格拉底愛好者：ai_chat_messages > 10
        2. 戰術型：錯題複習超過 3 次
        3. 馬拉松型：連續活躍 ≥ 14 天
        4. 衝刺型：連續活躍 ≥ 7 天 且 過去 7 日總答題 ≥ 100
        5. 反思型：超過 50% answers 有 user_confidence 紀錄
        6. 穩紮穩打型：累積 ≥ 5 份測驗
        7. 預設：成長型考生
        """
        type_id = self._pick_style(user_uuid)
        meta = _STYLE_DEFS[type_id]
        return {
            "type_id": type_id,
            "label": meta["label"],
            "emoji": meta["emoji"],
            "description": meta["description"],
        }

    def _pick_style(self, user_uuid: uuid.UUID) -> str:
        # 1. socratic — AI 對話訊息數
        try:
            from app.models.ai_chat import AiChatMessage, AiChatSession
            chat_count = (
                self.db.query(func.count(AiChatMessage.id))
                .join(AiChatSession, AiChatMessage.session_id == AiChatSession.id)
                .filter(AiChatSession.user_id == user_uuid, AiChatMessage.role == "user")
                .scalar()
                or 0
            )
            if chat_count > 10:
                return "socratic"
        except Exception:
            pass

        # 3. marathon
        streak = self._consecutive_active_days(user_uuid)
        if streak >= 14:
            return "marathon"

        # 4. sprint：streak ≥ 7 且 7 日內答題 ≥ 100
        if streak >= 7:
            from datetime import timedelta as _td
            recent_q = (
                self.db.query(func.count(Answer.id))
                .filter(
                    Answer.user_id == user_uuid,
                    Answer.answered_at >= datetime.now(timezone.utc) - _td(days=7),
                )
                .scalar()
                or 0
            )
            if recent_q >= 100:
                return "sprint"

        # 5. reflective：confidence 紀錄比例 > 50%
        try:
            total_a = self.db.query(func.count(Answer.id)).filter(Answer.user_id == user_uuid).scalar() or 0
            if total_a > 0:
                conf_a = (
                    self.db.query(func.count(Answer.id))
                    .filter(
                        Answer.user_id == user_uuid,
                        Answer.user_confidence.isnot(None),
                    )
                    .scalar()
                    or 0
                )
                if conf_a / total_a > 0.5:
                    return "reflective"
        except Exception:
            pass

        # 6. steady：≥ 5 份測驗
        if self._exam_count(user_uuid) >= 5:
            return "steady"

        # 預設
        return "explorer"
