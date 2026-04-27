"""Exam Repository — SQLAlchemy."""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.exam import Exam
import uuid


class ExamRepository:
    """考試（Exam）資料存取 Repository。

    封裝 Exam ORM 的儲存與查詢，供考試相關 service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, exam: Exam) -> None:
        """以 merge 方式新增或更新 Exam 並 commit。

        Args:
            exam: 待儲存的 Exam 實例。
        """
        self.session.merge(exam)
        self.session.commit()

    def find_by_id(self, exam_id: uuid.UUID) -> Optional[Exam]:
        """依 exam_id 查詢考試。

        Args:
            exam_id: 考試 UUID。

        Returns:
            Exam 物件；若不存在回傳 None。
        """
        return self.session.query(Exam).filter_by(id=exam_id).first()

    def find_latest_by_user(self, user_id: uuid.UUID) -> Optional[Exam]:
        """查詢使用者最新建立的一筆考試。

        Args:
            user_id: 使用者 UUID。

        Returns:
            最近一筆 Exam；若使用者尚無考試紀錄則回傳 None。
        """
        return self.session.query(Exam).filter_by(
            user_id=user_id
        ).order_by(Exam.created_at.desc()).first()
