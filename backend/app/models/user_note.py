"""User Note ORM Model — 對應 DBML user_notes 表。

Feature 50：我的筆記整合。
Migration 096：user_notes table。
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class UserNote(Base):
    """使用者自由格式筆記。

    對應 DBML 表：user_notes

    Business rules:
    - content 不可為空字串（CHECK ck_un_content_not_empty）
    - 必須綁定 subject（方便依科目分類）
    - node_id 可為 NULL（NULL = 科目層級自由筆記）
    - title 可為 NULL（可選短標題，最長 200 字）
    - 只有筆記擁有者能讀寫刪（service 層驗 user_id）

    Attributes:
        id: 主鍵 UUID
        user_id: 擁有者（CASCADE DELETE）
        subject_id: 科目（CASCADE DELETE）
        node_id: 知識節點（SET NULL，可選）
        title: 短標題（可選，最多 200 字）
        content: 筆記本文（不可空）
        created_at: 建立時間
        updated_at: 最後更新時間
    """

    __tablename__ = "user_notes"

    __table_args__ = (
        CheckConstraint("length(content) > 0", name="ck_un_content_not_empty"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=sa.func.now(),
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    subject = relationship("Subject", foreign_keys=[subject_id], lazy="select")
    knowledge_node = relationship(
        "KnowledgeNode", foreign_keys=[node_id], lazy="select"
    )
