"""Subject Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.subject import Subject, SubjectCategory


class SubjectRepository:
    """Subject Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, subject: Subject) -> Subject:
        """保存 Subject 到資料庫。"""
        self.session.add(subject)
        self.session.commit()
        self.session.refresh(subject)
        return subject

    def find_by_id(self, subject_id) -> Optional[Subject]:
        """根據 ID 查詢 Subject。"""
        return self.session.query(Subject).filter_by(id=subject_id).first()

    def find_by_name(self, name: str) -> Optional[Subject]:
        """根據名稱查詢 Subject。"""
        return self.session.query(Subject).filter_by(name=name).first()


class SubjectCategoryRepository:
    """SubjectCategory Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, category: SubjectCategory) -> SubjectCategory:
        """保存 SubjectCategory 到資料庫。"""
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category
