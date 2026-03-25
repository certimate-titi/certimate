"""User Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """User Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> User:
        """保存 User 到資料庫。"""
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def find_by_email(self, email: str) -> Optional[User]:
        """根據 email 查詢 User。"""
        return self.session.query(User).filter_by(email=email).first()

    def find_by_id(self, user_id) -> Optional[User]:
        """根據 ID 查詢 User。"""
        return self.session.query(User).filter_by(id=user_id).first()

    def delete_by_id(self, user_id) -> None:
        """根據 ID 刪除 User。"""
        user = self.find_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()

    def exists_by_email(self, email: str) -> bool:
        """檢查 email 是否已存在。"""
        return self.session.query(User).filter_by(email=email).count() > 0
