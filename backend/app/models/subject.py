"""Subject & SubjectCategory ORM Models — derived from erm.dbml."""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import DateTime, Integer, String, Text, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models import Base


class SubjectCategory(Base):
    __tablename__ = "subject_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subject_categories.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    parent_subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True
    )
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    available_questions: Mapped[int] = mapped_column(Integer, server_default="0")
    exam_subject_codes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True,
        comment="NULL = 平台 seed；UUID = 用戶自建考科的 owner",
    )
    scope: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="platform",
        comment="platform | personal | institution",
    )
    source_platform_subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True,
        comment="Fork 來源 platform subject — PRD-034",
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1",
        comment="僅 platform scope 有意義；admin publish +1",
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="platform 最近一次發布時間",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    parent: Mapped[Optional["Subject"]] = relationship(
        "Subject", remote_side="Subject.id", foreign_keys=[parent_subject_id],
        back_populates="children",
    )
    children: Mapped[List["Subject"]] = relationship(
        "Subject", back_populates="parent", foreign_keys="Subject.parent_subject_id",
    )
