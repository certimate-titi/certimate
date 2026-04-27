"""LearningJourney Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.learning_journey import LearningJourney


class LearningJourneyRepository:
    """學習歷程資料存取 Repository。

    封裝 LearningJourney ORM 的儲存與查詢；每位使用者在每個科目
    可有一筆學習歷程紀錄。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, journey: LearningJourney) -> LearningJourney:
        """新增或更新學習歷程並 commit。

        Args:
            journey: 待儲存的 LearningJourney 實例。

        Returns:
            已 refresh 的 LearningJourney 實例。
        """
        self.session.add(journey)
        self.session.commit()
        self.session.refresh(journey)
        return journey

    def find_by_user_and_subject(self, user_id, subject_id) -> Optional[LearningJourney]:
        """依使用者與科目查詢單一學習歷程。

        Args:
            user_id: 使用者 UUID。
            subject_id: 科目 UUID。

        Returns:
            LearningJourney 物件；若不存在回傳 None。
        """
        return self.session.query(LearningJourney).filter_by(
            user_id=user_id, subject_id=subject_id
        ).first()

    def find_by_user_id(self, user_id) -> list[LearningJourney]:
        """查詢使用者的所有科目學習歷程。

        Args:
            user_id: 使用者 UUID。

        Returns:
            list of LearningJourney，使用者尚無紀錄時回傳空 list。
        """
        return self.session.query(LearningJourney).filter_by(user_id=user_id).all()
