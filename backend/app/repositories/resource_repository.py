"""Resource Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.resource import Resource


class ResourceRepository:
    """資源（Resource）資料存取 Repository。

    封裝 Resource ORM 的儲存與查詢，供資源管理 service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, resource: Resource) -> Resource:
        """新增或更新資源並 commit。

        Args:
            resource: 待儲存的 Resource 實例。

        Returns:
            已 refresh 的 Resource 實例。
        """
        self.session.add(resource)
        self.session.commit()
        self.session.refresh(resource)
        return resource

    def find_by_id(self, resource_id) -> Optional[Resource]:
        """依 ID 查詢資源。

        Args:
            resource_id: Resource UUID。

        Returns:
            Resource 物件；若不存在回傳 None。
        """
        return self.session.query(Resource).filter_by(id=resource_id).first()
