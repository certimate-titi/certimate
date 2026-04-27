"""User Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """使用者資料存取 Repository。

    封裝 User ORM 的查詢、儲存、刪除邏輯，供 service 層使用。
    所有方法皆透過建構子注入的 SQLAlchemy Session 操作資料庫。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session，由 DI 容器注入。
        """
        self.session = session

    def save(self, user: User) -> User:
        """新增或更新 User 並 commit。

        Args:
            user: 待儲存的 User ORM 實例。

        Returns:
            已 refresh 的 User 實例（含 DB 產生的欄位，例如 id、created_at）。
        """
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def find_by_email(self, email: str) -> Optional[User]:
        """根據 email 查詢使用者。

        Args:
            email: 使用者 email。

        Returns:
            User 物件；若不存在回傳 None。
        """
        return self.session.query(User).filter_by(email=email).first()

    def find_by_id(self, user_id) -> Optional[User]:
        """根據 ID 查詢使用者。

        Args:
            user_id: 使用者 UUID。

        Returns:
            User 物件；若不存在回傳 None。
        """
        return self.session.query(User).filter_by(id=user_id).first()

    def delete_by_id(self, user_id) -> None:
        """根據 ID 永久刪除使用者。

        若使用者不存在則無動作。

        Args:
            user_id: 使用者 UUID。
        """
        user = self.find_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()

    def exists_by_email(self, email: str) -> bool:
        """檢查 email 是否已被註冊。

        Args:
            email: 待檢查的 email。

        Returns:
            True 表示已存在；False 表示尚未註冊。
        """
        return self.session.query(User).filter_by(email=email).count() > 0
