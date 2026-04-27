"""Question Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.question import Question
import uuid


class QuestionRepository:
    """題目資料存取 Repository。

    封裝 Question ORM 的儲存、查詢、軟/硬刪除與計數，供題目管理、
    出題、退役 service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, question: Question) -> Question:
        """新增或更新題目並 commit。

        Args:
            question: 待儲存的 Question 實例。

        Returns:
            已 refresh 的 Question 實例。
        """
        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)
        return question

    def find_by_id(self, question_id: uuid.UUID) -> Optional[Question]:
        """依 ID 查詢題目。

        Args:
            question_id: 題目 UUID。

        Returns:
            Question 物件；若不存在回傳 None。
        """
        return self.session.query(Question).filter_by(id=question_id).first()

    def find_by_exam_id(self, exam_id: uuid.UUID) -> list[Question]:
        """查詢考試的所有題目。

        Args:
            exam_id: Exam UUID。

        Returns:
            list of Question。
        """
        return self.session.query(Question).filter_by(exam_id=exam_id).all()

    def find_by_source_type(self, exam_id: uuid.UUID, source_type: str) -> list[Question]:
        """依考試與來源類型過濾題目。

        Args:
            exam_id: Exam UUID。
            source_type: 題目來源類型（例如 ``ai_generated``、``historical``）。

        Returns:
            list of Question。
        """
        return self.session.query(Question).filter_by(
            exam_id=exam_id, source_type=source_type
        ).all()

    def find_retired(self) -> list[Question]:
        """查詢所有已軟刪除（退役）的題目。

        Returns:
            list of Question，僅含 ``retired_at`` 非 NULL 的題目。
        """
        return self.session.query(Question).filter(
            Question.retired_at.isnot(None)
        ).all()

    def delete(self, question: Question) -> None:
        """永久刪除題目並 commit。

        Args:
            question: 待刪除的 Question 實例。
        """
        self.session.delete(question)
        self.session.commit()

    def count_by_subject_and_source(self, exam_ids: list, source_type: str) -> int:
        """計算特定考試清單與來源類型的有效題目數（排除退役題）。

        Args:
            exam_ids: Exam UUID 清單。
            source_type: 題目來源類型。

        Returns:
            符合條件且尚未退役的題目數量。
        """
        return self.session.query(Question).filter(
            Question.exam_id.in_(exam_ids),
            Question.source_type == source_type,
            Question.retired_at.is_(None),
        ).count()
