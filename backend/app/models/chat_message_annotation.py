"""Chat Message Annotation ORM Model — 對應 DBML chat_message_annotations。

Migration 095：AI 教練對話 highlight + 強制評語功能。
"""

from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class ChatMessageAnnotation(Base):
    """使用者對 AI 教練對話訊息的 highlight + 評語。

    對應 DBML 表：chat_message_annotations

    Business rules (enforced at DB + service + API):
    - user_annotation 最少 10 字（CHECK constraint ck_cma_annotation_min_len）
    - 同一 session 同一 user 最多 5 筆（service 層 max=5 守門）
    - user 只能標記自己的 session（service 層驗 session.user_id == user_id）

    Attributes:
        message_id: 對應 ai_chat_messages.id（CASCADE 刪除）
        user_id: 對應 users.id（CASCADE 刪除）
        session_id: 對應 ai_chat_sessions.id（CASCADE 刪除）
        highlighted_text: highlight 的原文片段
        user_annotation: 使用者的評語（≥10 字）
        annotation_type: note / key_insight / challenge / example / application
    """

    __tablename__ = "chat_message_annotations"

    __table_args__ = (
        CheckConstraint("length(user_annotation) >= 10", name="ck_cma_annotation_min_len"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    highlighted_text: Mapped[str] = mapped_column(Text, nullable=False)
    user_annotation: Mapped[str] = mapped_column(Text, nullable=False)
    annotation_type: Mapped[str] = mapped_column(
        Enum(
            "note",
            "key_insight",
            "challenge",
            "example",
            "application",
            name="annotation_type",
            create_type=False,
        ),
        nullable=False,
        server_default="note",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationships
    message = relationship("AiChatMessage", foreign_keys=[message_id], lazy="select")
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    session = relationship("AiChatSession", foreign_keys=[session_id], lazy="select")
    tags = relationship(
        "ChatAnnotationTag",
        foreign_keys="[ChatAnnotationTag.annotation_id]",
        back_populates="annotation",
        cascade="all, delete-orphan",
        lazy="select",
    )
