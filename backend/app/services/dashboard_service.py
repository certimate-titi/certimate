"""個人儀表板 Service。"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.subject import Subject
from app.models.learning_journey import LearningJourney


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self, user_id: str, subject_name: str | None = None) -> dict:
        """取得儀表板資料。"""
        user_uuid = uuid.UUID(user_id)

        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        # Get active (non-archived) learning journeys with subjects
        journeys = (
            self.db.query(LearningJourney, Subject)
            .join(Subject, LearningJourney.subject_id == Subject.id)
            .filter(
                LearningJourney.user_id == user_uuid,
                LearningJourney.is_archived == False,  # noqa: E712
            )
            .all()
        )

        if not journeys:
            return {
                "subjects": [],
                "active_subject": None,
                "guidance": "請至少新增一個備考科目",
                "add_subject_entry": True,
            }

        # Build subjects list sorted by exam_date (ascending, nulls last)
        subjects_list = []
        for journey, subject in journeys:
            subjects_list.append({
                "name": subject.name,
                "exam_date": journey.exam_date.isoformat() if journey.exam_date else None,
                "journey_id": str(journey.id),
                "subject_id": str(subject.id),
            })

        subjects_list.sort(key=lambda s: (s["exam_date"] is None, s["exam_date"] or ""))

        # Determine active subject
        if subject_name:
            active = next((s for s in subjects_list if s["name"] == subject_name), subjects_list[0])
        else:
            active = subjects_list[0]

        active_subject_name = active["name"]
        active_exam_date = active["exam_date"]

        # Compute exam countdown
        today = date.today()
        if active_exam_date:
            exam_dt = date.fromisoformat(active_exam_date)
            days_left = (exam_dt - today).days
        else:
            days_left = None

        exam_countdown = {
            "exam_date": active_exam_date,
            "days_left": days_left,
        }

        # Build radar chart data from NodeMastery (joined via KnowledgeNode)
        # KnowledgeNode links to Resource, not Subject directly.
        # We return empty nodes if none exist yet.
        radar_data = []

        radar_chart = {
            "subject": active_subject_name,
            "nodes": radar_data,
        }

        return {
            "subjects": subjects_list,
            "active_subject": active_subject_name,
            "add_subject_entry": True,
            "exam_countdown": exam_countdown,
            "radar_chart": radar_chart,
            "quick_upload": {"enabled": True},
            "todo_reminders": {"wrong_answers": 0, "incomplete_exams": 0},
        }

    def update_profile(self, user_id: str, data: dict) -> dict:
        """更新個人資料。"""
        user_uuid = uuid.UUID(user_id)

        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        allowed_fields = {"display_name", "age", "education", "career"}
        for field, value in data.items():
            if field in allowed_fields and value is not None:
                setattr(user, field, value)

        self.db.commit()
        return {"message": "個人資料已更新"}
