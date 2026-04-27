"""NodeMastery Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.node_mastery import NodeMastery


class NodeMasteryRepository:
    """知識節點掌握度資料存取 Repository。

    封裝 NodeMastery ORM 的儲存與查詢；每位使用者對每個知識節點
    可有一筆掌握度紀錄。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, mastery: NodeMastery) -> NodeMastery:
        """新增或更新掌握度紀錄並 commit。

        Args:
            mastery: 待儲存的 NodeMastery 實例。

        Returns:
            已 refresh 的 NodeMastery 實例。
        """
        self.session.add(mastery)
        self.session.commit()
        self.session.refresh(mastery)
        return mastery

    def find_by_user_and_node(self, user_id, node_id) -> Optional[NodeMastery]:
        """依使用者與知識節點查詢單一掌握度紀錄。

        Args:
            user_id: 使用者 UUID。
            node_id: KnowledgeNode UUID。

        Returns:
            NodeMastery 物件；若不存在回傳 None。
        """
        return self.session.query(NodeMastery).filter_by(
            user_id=user_id, node_id=node_id
        ).first()

    def find_by_user_id(self, user_id) -> list[NodeMastery]:
        """查詢使用者的所有掌握度紀錄。

        Args:
            user_id: 使用者 UUID。

        Returns:
            list of NodeMastery，使用者尚無紀錄時回傳空 list。
        """
        return self.session.query(NodeMastery).filter_by(user_id=user_id).all()
