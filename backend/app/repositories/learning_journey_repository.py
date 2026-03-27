"""LearningJourney Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.learning_journey import LearningJourney


class LearningJourneyRepository:
    """LearningJourney Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, journey: LearningJourney) -> LearningJourney:
        """保存 LearningJourney 到資料庫。"""
        self.session.add(journey)
        self.session.commit()
        self.session.refresh(journey)
        return journey

    def find_by_user_and_subject(self, user_id, subject_id) -> Optional[LearningJourney]:
        """根據 user_id 和 subject_id 查詢。"""
        return self.session.query(LearningJourney).filter_by(
            user_id=user_id, subject_id=subject_id
        ).first()

    def find_by_user_id(self, user_id) -> list[LearningJourney]:
        """根據 user_id 查詢所有學習歷程。"""
        return self.session.query(LearningJourney).filter_by(user_id=user_id).all()
