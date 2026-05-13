"""ChatAnnotationTag ORM Model — 對應 DBML chat_annotation_tags 表。

Feature 54：tag 系統涵蓋 3 sources（user_notes / chat_annotations / scaffold user_response）。
Migration 098：chat_annotation_tags table。
"""

import uuid as _uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class ChatAnnotationTag(Base):
    """Chat Annotation hashtag 標籤，以 Obsidian-style `#word` 從 user_annotation 解析。

    對應 DBML 表：chat_annotation_tags

    Business rules:
    - 複合 PK (annotation_id, tag_normalized)
    - tag_normalized：lowercase trimmed，用於 index/dedup
    - tag_display：user 原始輸入（first occurrence preserved）
    - CASCADE DELETE 隨 chat_message_annotations.id 刪除

    Attributes:
        annotation_id: 標記 UUID（FK → chat_message_annotations.id CASCADE DELETE）
        tag_normalized: 正規化 tag（lowercase，最多 64 字）
        tag_display: 顯示用原文（最多 80 字）
    """

    __tablename__ = "chat_annotation_tags"

    annotation_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_message_annotations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    tag_normalized: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        nullable=False,
    )
    tag_display: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    # Relationship back to ChatMessageAnnotation
    annotation = relationship(
        "ChatMessageAnnotation",
        foreign_keys=[annotation_id],
        back_populates="tags",
        lazy="select",
    )
