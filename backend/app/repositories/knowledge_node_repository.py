"""KnowledgeNode Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.knowledge_node import KnowledgeNode


class KnowledgeNodeRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, node: KnowledgeNode) -> KnowledgeNode:
        self.session.add(node)
        self.session.commit()
        self.session.refresh(node)
        return node

    def find_by_id(self, node_id) -> Optional[KnowledgeNode]:
        return self.session.query(KnowledgeNode).filter_by(id=node_id).first()

    def find_by_resource_id(self, resource_id) -> list[KnowledgeNode]:
        return self.session.query(KnowledgeNode).filter_by(
            resource_id=resource_id
        ).order_by(KnowledgeNode.depth, KnowledgeNode.sort_order).all()

    def find_leaves_by_resource_id(self, resource_id) -> list[KnowledgeNode]:
        """找出所有葉節點（沒有子節點的節點）。"""
        subquery = self.session.query(KnowledgeNode.parent_id).filter(
            KnowledgeNode.parent_id.isnot(None)
        ).subquery()
        return self.session.query(KnowledgeNode).filter(
            KnowledgeNode.resource_id == resource_id,
            ~KnowledgeNode.id.in_(subquery)
        ).all()
