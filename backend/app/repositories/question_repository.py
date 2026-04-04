"""Question Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.question import Question
import uuid


class QuestionRepository:
    """Question Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, question: Question) -> Question:
        """保存 Question 到資料庫。"""
        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)
        return question

    def find_by_id(self, question_id: uuid.UUID) -> Optional[Question]:
        """根據 ID 查詢 Question。"""
        return self.session.query(Question).filter_by(id=question_id).first()

    def find_by_exam_id(self, exam_id: uuid.UUID) -> list[Question]:
        """根據 exam_id 查詢所有題目。"""
        return self.session.query(Question).filter_by(exam_id=exam_id).all()

    def find_by_source_type(self, exam_id: uuid.UUID, source_type: str) -> list[Question]:
        """根據 exam_id 和 source_type 查詢。"""
        return self.session.query(Question).filter_by(
            exam_id=exam_id, source_type=source_type
        ).all()

    def find_retired(self) -> list[Question]:
        """查詢所有已軟刪除的題目。"""
        return self.session.query(Question).filter(
            Question.retired_at.isnot(None)
        ).all()

    def delete(self, question: Question) -> None:
        """永久刪除 Question。"""
        self.session.delete(question)
        self.session.commit()

    def count_by_subject_and_source(self, exam_ids: list, source_type: str) -> int:
        """計算特定來源類型的題目數量。"""
        return self.session.query(Question).filter(
            Question.exam_id.in_(exam_ids),
            Question.source_type == source_type,
            Question.retired_at.is_(None),
        ).count()
