"""ScaffoldTag ORM Model — 對應 DBML scaffold_tags 表。

Feature 54：tag 系統涵蓋 3 sources（user_notes / chat_annotations / scaffold user_response）。
Migration 099：scaffold_tags table。
"""

import uuid as _uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class ScaffoldTag(Base):
    """Scaffold user_response hashtag 標籤，以 Obsidian-style `#word` 從 user_response 解析。

    對應 DBML 表：scaffold_tags

    Business rules:
    - 複合 PK (scaffold_id, user_id, tag_normalized)
    - user_id 冗餘欄位，避免 join resources 才能 filter（效能考量）
    - tag_normalized：lowercase trimmed，用於 index/dedup
    - tag_display：user 原始輸入（first occurrence preserved）
    - CASCADE DELETE 隨 resource_scaffolds.id / users.id 刪除

    Attributes:
        scaffold_id: 鷹架 UUID（FK → resource_scaffolds.id CASCADE DELETE）
        user_id: 作答 user UUID（FK → users.id CASCADE DELETE，冗餘欄位）
        tag_normalized: 正規化 tag（lowercase，最多 64 字）
        tag_display: 顯示用原文（最多 80 字）
    """

    __tablename__ = "scaffold_tags"

    scaffold_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resource_scaffolds.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
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

    # Relationships
    scaffold = relationship(
        "ResourceScaffold",
        foreign_keys=[scaffold_id],
        back_populates="tags",
        lazy="select",
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="select",
    )
