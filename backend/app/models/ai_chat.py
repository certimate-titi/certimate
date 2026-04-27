"""AI Chat ORM Models — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class AiChatSession(Base):
    """AI 對話 Session（一個使用者在某個情境下開啟的對話串）。

    對應 DBML 表：ai_chat_sessions
    一對多關聯 ai_chat_messages（透過 session_id）。

    Attributes:
        user_id: 對應 users.id（CASCADE 刪除）
        context_type: 情境類型（例如 question / resource / mock_exam）
        context_id: 情境主鍵 UUID（依 context_type 解讀）
        model_used: 採用的 AI 模型名稱（例如 gemini-2.5-pro）
        message_count: 目前累積訊息數
        tenant_id: 多租戶隔離鍵（NULL 視為 public_b2c）
    """

    __tablename__ = "ai_chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    context_type: Mapped[str] = mapped_column(String(20), nullable=False)
    context_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(50))
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="多租戶隔離鍵（NULL = 歸屬 public_b2c）",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AiChatMessage(Base):
    """AI 對話單則訊息。

    對應 DBML 表：ai_chat_messages
    從屬於 AiChatSession（session_id CASCADE 刪除）。

    Attributes:
        session_id: 所屬 session
        role: 訊息角色（user / assistant / system）
        content: 訊息文字內容
        token_count: 該訊息所耗 token 數（供成本帳明細）
    """

    __tablename__ = "ai_chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
