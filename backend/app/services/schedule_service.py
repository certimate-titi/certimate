"""學習記憶排程 Service。"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject


class ScheduleService:
    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(self, user_id: str):
        """查看學習排程建議。"""
        user_uuid = uuid.UUID(user_id)

        journeys = (
            self.db.query(LearningJourney, Subject)
            .join(Subject, Subject.id == LearningJourney.subject_id)
            .filter(LearningJourney.user_id == user_uuid)
            .filter(LearningJourney.is_archived == False)  # noqa: E712
            .all()
        )

        if not journeys:
            return {"error": True, "status_code": 400, "message": "請先在 Onboarding 或會員中心新增至少一個備考科目"}

        subjects = []
        for journey, subj in journeys:
            mode = self._calculate_mode(journey.exam_date, date.today())
            subjects.append({
                "subject_name": subj.name,
                "exam_date": journey.exam_date.isoformat() if journey.exam_date else None,
                "learning_mode": mode,
            })

        return {"subjects": subjects}

    def init_schedule(self, user_id: str, subject_id: str):
        """初始化排程。"""
        user_uuid = uuid.UUID(user_id)
        subj_uuid = uuid.UUID(subject_id)

        journey = self.db.query(LearningJourney).filter_by(
            user_id=user_uuid, subject_id=subj_uuid
        ).first()

        if not journey:
            return {"error": True, "status_code": 404, "message": "找不到該科目的學習歷程"}

        if not journey.exam_date:
            return {"error": True, "status_code": 400, "message": "必須設定考試日期才能初始化排程"}

        mode = self._calculate_mode(journey.exam_date, date.today())
        return {"message": "排程初始化完成", "learning_mode": mode}

    def calculate_mode(self, user_id: str, subject_id: str, today_str: str | None = None):
        """計算學習模式。"""
        user_uuid = uuid.UUID(user_id)
        subj_uuid = uuid.UUID(subject_id)

        journey = self.db.query(LearningJourney).filter_by(
            user_id=user_uuid, subject_id=subj_uuid
        ).first()

        if not journey:
            return {"error": True, "status_code": 404, "message": "找不到該科目的學習歷程"}

        today = date.fromisoformat(today_str) if today_str else date.today()
        mode = self._calculate_mode(journey.exam_date, today)

        return {"learning_mode": mode}

    def _calculate_mode(self, exam_date: date | None, today: date) -> str:
        """根據距考日天數計算學習模式。"""
        if not exam_date:
            return "standard"

        days_until = (exam_date - today).days

        if days_until <= 14:
            return "sprint"
        elif days_until <= 180:  # ~6 months
            return "standard"
        else:
            return "mastery"
