"""MaintenanceNotification ORM Model — derived from erm.dbml maintenance_notifications table."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class MaintenanceNotification(Base):
    """系統維護預告通知排程紀錄。

    對應 DBML 表：maintenance_notifications

    Attributes:
        schedule_id: 對應 maintenance_schedules.id
        scheduled_send_at: 預定發送時間
        sent_at: 實際發送時間（NULL = 尚未送出）
    """

    __tablename__ = "maintenance_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    scheduled_send_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
