"""AiChat Repository — SQLAlchemy implementation."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.ai_chat import AiChatSession, AiChatMessage


class AiChatSessionRepository:
    """AiChatSession Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, chat_session: AiChatSession) -> AiChatSession:
        """保存 AiChatSession 到資料庫。"""
        self.session.add(chat_session)
        self.session.commit()
        self.session.refresh(chat_session)
        return chat_session

    def find_by_user_and_context(self, user_id, context_type: str, context_id) -> Optional[AiChatSession]:
        """根據 user_id、context_type、context_id 查詢。"""
        return self.session.query(AiChatSession).filter_by(
            user_id=user_id, context_type=context_type, context_id=context_id
        ).first()


class AiChatMessageRepository:
    """AiChatMessage Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, message: AiChatMessage) -> AiChatMessage:
        """保存 AiChatMessage 到資料庫。"""
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def count_by_session(self, session_id) -> int:
        """計算 session 中的訊息數量。"""
        return self.session.query(AiChatMessage).filter_by(session_id=session_id).count()
