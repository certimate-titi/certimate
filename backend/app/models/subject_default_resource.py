"""SubjectDefaultResource ORM — Migration 062 (PRD-033 §6.2)."""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class SubjectDefaultResource(Base):
    """科目預設資源關聯（PRD-033 §6.2）。

    對應 DBML 表：subject_default_resources
    複合主鍵（subject_id, resource_id），用於指派各科目開卷預設可見資源。

    Attributes:
        subject_id: 所屬科目（CASCADE）
        resource_id: 預設資源（CASCADE）
        added_by_user_id: 加入者（SET NULL）
        added_at: 加入時間
    """

    __tablename__ = "subject_default_resources"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        primary_key=True,
    )
    added_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
