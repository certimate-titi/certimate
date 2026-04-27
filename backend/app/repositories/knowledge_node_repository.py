"""KnowledgeNode Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.knowledge_node import KnowledgeNode


class KnowledgeNodeRepository:
    """知識節點資料存取 Repository。

    封裝 KnowledgeNode ORM 的儲存與樹狀查詢，供知識地圖 service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, node: KnowledgeNode) -> KnowledgeNode:
        """新增或更新知識節點並 commit。

        Args:
            node: 待儲存的 KnowledgeNode 實例。

        Returns:
            已 refresh 的 KnowledgeNode 實例。
        """
        self.session.add(node)
        self.session.commit()
        self.session.refresh(node)
        return node

    def find_by_id(self, node_id) -> Optional[KnowledgeNode]:
        """依 node_id 查詢知識節點。

        Args:
            node_id: KnowledgeNode UUID。

        Returns:
            KnowledgeNode 物件；若不存在回傳 None。
        """
        return self.session.query(KnowledgeNode).filter_by(id=node_id).first()

    def find_by_resource_id(self, resource_id) -> list[KnowledgeNode]:
        """查詢資源底下所有知識節點，依 depth、sort_order 升冪排序。

        Args:
            resource_id: Resource UUID。

        Returns:
            list of KnowledgeNode。
        """
        return self.session.query(KnowledgeNode).filter_by(
            resource_id=resource_id
        ).order_by(KnowledgeNode.depth, KnowledgeNode.sort_order).all()

    def find_leaves_by_resource_id(self, resource_id) -> list[KnowledgeNode]:
        """找出資源底下所有葉節點（沒有子節點的節點）。

        Args:
            resource_id: Resource UUID。

        Returns:
            list of KnowledgeNode，僅含葉節點。
        """
        subquery = self.session.query(KnowledgeNode.parent_id).filter(
            KnowledgeNode.parent_id.isnot(None)
        ).subquery()
        return self.session.query(KnowledgeNode).filter(
            KnowledgeNode.resource_id == resource_id,
            ~KnowledgeNode.id.in_(subquery)
        ).all()
