"""學習歷程 Service — 考試結果確認。"""

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.learning_journey import LearningJourney
from app.models.question import Question
from app.models.exam import Exam
from app.models.subject import Subject


class LearningJourneyService:
    def __init__(self, db: Session):
        self.db = db

    def list_pending(self, user_id: str):
        """列出需要使用者確認結果的學習歷程：放榜日已到且尚未確認。"""
        u_uuid = uuid.UUID(user_id)
        today = date.today()
        journeys = (
            self.db.query(LearningJourney)
            .filter(
                LearningJourney.user_id == u_uuid,
                LearningJourney.is_archived == False,  # noqa: E712
                LearningJourney.result_date.isnot(None),
                LearningJourney.result_date <= today,
            )
            .all()
        )
        items = []
        for j in journeys:
            if j.exam_result_status in ("passed", "quit"):
                continue
            subject = self.db.query(Subject).filter_by(id=j.subject_id).first()
            items.append({
                "id": str(j.id),
                "subject_id": str(j.subject_id),
                "subject_name": subject.name if subject else "",
                "exam_date": j.exam_date.isoformat() if j.exam_date else None,
                "result_date": j.result_date.isoformat() if j.result_date else None,
                "exam_result_status": j.exam_result_status,
            })
        return {"items": items}

    def confirm_exam_result(self, journey_id: str, status: str):
        """確認考試結果（passed/failed）。"""
        j_uuid = uuid.UUID(journey_id)
        journey = self.db.query(LearningJourney).filter_by(id=j_uuid).first()
        if not journey:
            return {"error": True, "status_code": 404, "message": "學習歷程不存在"}

        journey.exam_result_status = status
        today = date.today()

        if status == "passed":
            journey.data_expiry_date = today + timedelta(days=7)
            self.db.commit()
            subject = self.db.query(Subject).filter_by(id=journey.subject_id).first()
            # 推薦相關證照
            recommendations = []
            if subject:
                related = (
                    self.db.query(Subject)
                    .filter(
                        Subject.category_id == subject.category_id,
                        Subject.id != subject.id,
                    )
                    .limit(3)
                    .all()
                )
                recommendations = [{"id": str(s.id), "name": s.name} for s in related]

            return {
                "exam_result_status": status,
                "data_expiry_date": journey.data_expiry_date.isoformat(),
                "notification_type": "congrats",
                "type": "passed",
                "recommendations": recommendations,
                "subjects": recommendations,
                "content": f"恭喜考取！資料將保留 7 天",
            }

        elif status == "failed":
            self.db.commit()
            return {
                "exam_result_status": status,
                "notification_type": "encourage",
                "type": "encourage",
                "content": "不要灰心！是否再次報考？",
                "actions": [
                    {"label": "再次報考", "action": "retake"},
                    {"label": "不再報考", "action": "quit"},
                ],
            }

        self.db.commit()
        return {"exam_result_status": status}

    def retake(self, journey_id: str, exam_date: str | None, result_date: str | None):
        """選擇再次報考。"""
        j_uuid = uuid.UUID(journey_id)
        journey = self.db.query(LearningJourney).filter_by(id=j_uuid).first()
        if not journey:
            return {"error": True, "status_code": 404, "message": "學習歷程不存在"}

        journey.exam_result_status = "retake"
        journey.data_expiry_date = None

        if exam_date:
            journey.exam_date = date.fromisoformat(exam_date)
        if result_date:
            journey.result_date = date.fromisoformat(result_date)

        # 恢復軟刪除的 AI 題（90 天內）
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=90)
        exams = self.db.query(Exam).filter_by(
            user_id=journey.user_id,
            subject_id=journey.subject_id,
        ).all()
        for exam in exams:
            questions = (
                self.db.query(Question)
                .filter(
                    Question.exam_id == exam.id,
                    Question.source_type == "ai_generated",
                    Question.retired_at.isnot(None),
                    Question.retired_at > cutoff,
                )
                .all()
            )
            for q in questions:
                q.retired_at = None
                q.retention_reason = None

        self.db.commit()

        return {
            "exam_result_status": "retake",
            "exam_date": journey.exam_date.isoformat() if journey.exam_date else None,
            "result_date": journey.result_date.isoformat() if journey.result_date else None,
            "learning_plan_updated": True,
        }

    def quit(self, journey_id: str):
        """選擇不再報考。"""
        j_uuid = uuid.UUID(journey_id)
        journey = self.db.query(LearningJourney).filter_by(id=j_uuid).first()
        if not journey:
            return {"error": True, "status_code": 404, "message": "學習歷程不存在"}

        journey.exam_result_status = "quit"
        journey.data_expiry_date = date.today() + timedelta(days=30)
        self.db.commit()

        return {
            "exam_result_status": "quit",
            "data_expiry_date": journey.data_expiry_date.isoformat(),
            "notification_type": "farewell",
            "type": "farewell",
            "content": f"感謝使用 TiTi！資料將保留 30 天",
        }

    def update_result_date(self, journey_id: str, result_date: str):
        """更新放榜日期。"""
        j_uuid = uuid.UUID(journey_id)
        journey = self.db.query(LearningJourney).filter_by(id=j_uuid).first()
        if not journey:
            return {"error": True, "status_code": 404, "message": "學習歷程不存在"}

        journey.result_date = date.fromisoformat(result_date)
        self.db.commit()

        return {
            "result_date": journey.result_date.isoformat(),
        }
