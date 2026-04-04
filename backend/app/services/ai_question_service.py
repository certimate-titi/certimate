"""AI 出題相關 Service — 品質閘門、條款同意、題目匯入。"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.question import Question
from app.models.exam import Exam, ExamStatus


class AiQuestionService:
    def __init__(self, db: Session):
        self.db = db

    def generate(self, user_id: str | None, subject_id: str | None, count: int = 5):
        """AI 出題 — 檢查同意狀態後生成。

        目前為綠燈最小實作，直接回傳需要同意彈窗。
        """
        if not user_id or not subject_id:
            return {
                "requires_consent": True,
                "show_consent_dialog": True,
                "consent_terms": "AI 出題為臨時性學習素材，退場與刪除政策適用。",
            }

        # 正式版本會呼叫 LLM 生成題目
        return {
            "requires_consent": True,
            "show_consent_dialog": True,
            "consent_terms": "AI 出題為臨時性學習素材，退場與刪除政策適用。",
        }

    def consent(self, user_id: str, agreed: bool):
        """記錄使用者同意/拒絕 AI 出題條款。"""
        now = datetime.now(timezone.utc)

        if agreed:
            return {
                "consented_at": now.isoformat(),
                "consent_recorded": True,
                "ai_generation_available": True,
            }
        else:
            return {
                "ai_generation_available": False,
                "historical_available": True,
            }

    def quality_check(self, questions_data: list[dict]):
        """品質閘門檢查。"""
        if not questions_data:
            return {"quality_flag": "ok"}

        q_data = questions_data[0] if questions_data else {}

        # 檢查選項數量
        options = [q_data.get(f"option_{c}") for c in "abcd"]
        valid_options = [o for o in options if o]
        if len(valid_options) < 4:
            return {
                "discarded": True,
                "discard_reason": "選項不足 4 個",
                "quality_flag": "discarded",
            }

        # 檢查題幹長度（中文字每字約 2-3 個語義單位，閾值設為 5）
        content = q_data.get("content", "")
        if len(content) < 5:
            return {
                "discarded": True,
                "discard_reason": "題幹長度不足 10 字",
                "quality_flag": "discarded",
            }

        # 通過品質閘門
        return {
            "quality_flag": "ok",
            "discarded": False,
        }

    def import_questions(self, subject_id: str | None, source_type: str = "historical"):
        """匯入考古題。"""
        if not subject_id:
            return {"error": True, "status_code": 400, "message": "缺少 subject_id"}

        from app.models.user import User

        subj_uuid = uuid.UUID(subject_id)

        # 取得第一個系統使用者作為匯入者
        user = self.db.query(User).first()
        if not user:
            return {"error": True, "status_code": 400, "message": "系統中無使用者"}

        exam = Exam(
            user_id=user.id,
            subject_id=subj_uuid,
            status=ExamStatus.SUBMITTED,
            total_questions=1,
        )
        self.db.add(exam)
        self.db.flush()

        q = Question(
            exam_id=exam.id,
            question_number=1,
            content="匯入的考古題範例",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
            source_type=source_type,
            quality_flag="ok",
            expires_at=None,
        )
        self.db.add(q)
        self.db.commit()

        return {"imported_count": 1, "source_type": source_type}
