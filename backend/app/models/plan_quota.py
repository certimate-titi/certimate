"""PlanQuota ORM Model — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class PlanQuota(Base):
    __tablename__ = "plan_quotas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    monthly_uploads: Mapped[int | None] = mapped_column(Integer)
    monthly_exams: Mapped[int | None] = mapped_column(Integer)
    daily_ai_chats: Mapped[int | None] = mapped_column(Integer)
    monthly_vision_pages: Mapped[int | None] = mapped_column(Integer)
    max_file_size_mb: Mapped[int | None] = mapped_column(Integer)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
