"""AiChat Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.ai_chat import AiChatSession, AiChatMessage


class AiChatSessionRepository:
    """AI 對話 Session 資料存取 Repository。

    封裝 AiChatSession ORM 的查詢與儲存邏輯，供 AI Chat service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, chat_session: AiChatSession) -> AiChatSession:
        """新增或更新 AiChatSession 並 commit。

        Args:
            chat_session: 待儲存的 AiChatSession 實例。

        Returns:
            已 refresh 的 AiChatSession 實例。
        """
        self.session.add(chat_session)
        self.session.commit()
        self.session.refresh(chat_session)
        return chat_session

    def find_by_user_and_context(self, user_id, context_type: str, context_id) -> Optional[AiChatSession]:
        """依使用者與上下文情境查詢 AI 對話 Session。

        Args:
            user_id: 使用者 UUID。
            context_type: 對話情境類型（例如 resource、knowledge_node）。
            context_id: 對應情境主體 UUID。

        Returns:
            AiChatSession 物件；若不存在回傳 None。
        """
        return self.session.query(AiChatSession).filter_by(
            user_id=user_id, context_type=context_type, context_id=context_id
        ).first()


class AiChatMessageRepository:
    """AI 對話訊息資料存取 Repository。

    封裝 AiChatMessage ORM 的儲存與計數邏輯。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, message: AiChatMessage) -> AiChatMessage:
        """新增或更新 AiChatMessage 並 commit。

        Args:
            message: 待儲存的 AiChatMessage 實例。

        Returns:
            已 refresh 的 AiChatMessage 實例。
        """
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def count_by_session(self, session_id) -> int:
        """統計指定 Session 內的訊息數量。

        Args:
            session_id: AiChatSession UUID。

        Returns:
            該 Session 訊息總數。
        """
        return self.session.query(AiChatMessage).filter_by(session_id=session_id).count()
