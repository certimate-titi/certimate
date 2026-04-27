"""Subject Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.subject import Subject, SubjectCategory


class SubjectRepository:
    """科目資料存取 Repository。

    封裝 Subject ORM 的儲存與查詢，供科目管理 service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, subject: Subject) -> Subject:
        """新增或更新科目並 commit。

        Args:
            subject: 待儲存的 Subject 實例。

        Returns:
            已 refresh 的 Subject 實例。
        """
        self.session.add(subject)
        self.session.commit()
        self.session.refresh(subject)
        return subject

    def find_by_id(self, subject_id) -> Optional[Subject]:
        """依 ID 查詢科目。

        Args:
            subject_id: Subject UUID。

        Returns:
            Subject 物件；若不存在回傳 None。
        """
        return self.session.query(Subject).filter_by(id=subject_id).first()

    def find_by_name(self, name: str) -> Optional[Subject]:
        """依名稱查詢科目。

        Args:
            name: 科目名稱。

        Returns:
            Subject 物件；若不存在回傳 None。
        """
        return self.session.query(Subject).filter_by(name=name).first()


class SubjectCategoryRepository:
    """科目分類資料存取 Repository。

    封裝 SubjectCategory ORM 的儲存。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, category: SubjectCategory) -> SubjectCategory:
        """新增或更新科目分類並 commit。

        Args:
            category: 待儲存的 SubjectCategory 實例。

        Returns:
            已 refresh 的 SubjectCategory 實例。
        """
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category
