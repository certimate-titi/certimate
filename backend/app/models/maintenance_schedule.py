"""MaintenanceSchedule ORM Model — derived from erm.dbml maintenance_schedules table."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class MaintenanceScheduleStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"


class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=MaintenanceScheduleStatus.SCHEDULED, nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    notify_channels: Mapped[list | None] = mapped_column(
        ARRAY(String), server_default="{}"
    )
    notify_targets: Mapped[str | None] = mapped_column(String(100))
    notify_before: Mapped[list | None] = mapped_column(
        ARRAY(String), server_default="{}"
    )
    reason: Mapped[str | None] = mapped_column(Text)
    is_full_site: Mapped[bool] = mapped_column(Boolean, default=False)
    health_check_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
