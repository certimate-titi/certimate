"""NodeMastery Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.node_mastery import NodeMastery


class NodeMasteryRepository:
    """NodeMastery Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, mastery: NodeMastery) -> NodeMastery:
        """保存 NodeMastery 到資料庫。"""
        self.session.add(mastery)
        self.session.commit()
        self.session.refresh(mastery)
        return mastery

    def find_by_user_and_node(self, user_id, node_id) -> Optional[NodeMastery]:
        """根據 user_id 和 node_id 查詢。"""
        return self.session.query(NodeMastery).filter_by(
            user_id=user_id, node_id=node_id
        ).first()

    def find_by_user_id(self, user_id) -> list[NodeMastery]:
        """根據 user_id 查詢所有掌握度。"""
        return self.session.query(NodeMastery).filter_by(user_id=user_id).all()
