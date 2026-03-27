"""Exam Repository — SQLAlchemy."""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.exam import Exam
import uuid


class ExamRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, exam: Exam) -> None:
        self.session.merge(exam)
        self.session.commit()

    def find_by_id(self, exam_id: uuid.UUID) -> Optional[Exam]:
        return self.session.query(Exam).filter_by(id=exam_id).first()

    def find_latest_by_user(self, user_id: uuid.UUID) -> Optional[Exam]:
        return self.session.query(Exam).filter_by(
            user_id=user_id
        ).order_by(Exam.created_at.desc()).first()
