"""UserNoteTag ORM Model — 對應 DBML user_note_tags 表。

Feature 52：筆記 hashtag 系統。
Migration 097：user_note_tags table。
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class UserNoteTag(Base):
    """筆記 hashtag 標籤，以 Obsidian-style `#word` 從 markdown content 解析。

    對應 DBML 表：user_note_tags

    Business rules:
    - 複合 PK (note_id, tag_normalized)
    - tag_normalized：lowercase trimmed，用於 index/dedup
    - tag_display：user 原始輸入（first occurrence preserved）
    - CASCADE DELETE 隨 user_notes.id 刪除

    Attributes:
        note_id: 筆記 UUID（FK → user_notes.id CASCADE DELETE）
        tag_normalized: 正規化 tag（lowercase，最多 64 字）
        tag_display: 顯示用原文（最多 80 字）
    """

    __tablename__ = "user_note_tags"

    note_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user_notes.id", ondelete="CASCADE"),
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

    # Relationship back to UserNote
    note = relationship(
        "UserNote",
        foreign_keys=[note_id],
        back_populates="tags",
        lazy="select",
    )
