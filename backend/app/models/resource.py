"""Resource ORM Model — derived from erm.dbml."""

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class ResourceType(str, enum.Enum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TXT = "txt"
    IMAGE = "image"
    YOUTUBE = "youtube"


class ResourceStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_NO_MAP = "COMPLETED_NO_MAP"
    FAILED = "FAILED"
    DELETED = "DELETED"


class ResourceScope(str, enum.Enum):
    PERSONAL = "personal"
    INSTITUTION = "institution"


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id")
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum(ResourceType, name="resource_type", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    scope: Mapped[str] = mapped_column(
        Enum(ResourceScope, name="resource_scope", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=ResourceScope.PERSONAL,
    )
    status: Mapped[str] = mapped_column(
        Enum(ResourceStatus, name="resource_status", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=ResourceStatus.PENDING,
    )
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    gcs_path: Mapped[str | None] = mapped_column(Text)
    youtube_url: Mapped[str | None] = mapped_column(Text)
    processing_engine: Mapped[str | None] = mapped_column(String(50))
    implicit_consent: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[list | None] = mapped_column(JSON, server_default="[]")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
