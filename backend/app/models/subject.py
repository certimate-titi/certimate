"""Subject & SubjectCategory ORM Models — derived from erm.dbml."""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import DateTime, Integer, String, Text, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models import Base


class SubjectCategory(Base):
    """科目分類（例如 國家考試 / 證照 / 升學）。

    對應 DBML 表：subject_categories

    Attributes:
        name: 分類名稱
        sort_order: 顯示順序
    """

    __tablename__ = "subject_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Subject(Base):
    """科目實體（含平台 seed / 用戶自建 / 機構自建）。

    對應 DBML 表：subjects
    自關聯（parent_subject_id）形成階層；fork 來源由 source_platform_subject_id 追蹤。
    與 resources / questions / knowledge_nodes 一對多。

    Attributes:
        category_id: 所屬 SubjectCategory
        name / name_en / description: 顯示資訊
        parent_subject_id: 父科目（階層）
        is_popular: 是否熱門
        available_questions: 可用題數快取
        exam_subject_codes: JSONB 對應考試科目代碼清單
        owner_user_id: NULL = 平台 seed；UUID = 用戶自建擁有者（CASCADE）
        scope: platform / personal / institution
        source_platform_subject_id: Fork 來源平台科目（PRD-034）
        version: 平台版本（admin publish +1）
        published_at: 平台最近發布時間
    """

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
