"""MaintenanceTask ORM Model — derived from erm.dbml maintenance_tasks table."""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class MaintenancePriority(str, enum.Enum):
    """維運任務優先級列舉。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MaintenanceTaskStatus(str, enum.Enum):
    """維運任務處理狀態列舉。"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenanceTask(Base):
    """維運工單（追蹤 incident 修復、技術債等）。

    對應 DBML 表：maintenance_tasks

    Attributes:
        task_id: 對外案件編號（unique）
        name: 任務名稱
        priority: low / medium / high / critical
        related_error_id: 關聯的 anomaly_records.id（可空）
        status: pending / in_progress / completed / cancelled
        estimated_hours: 預估工時
        created_by / assigned_to: 建立者與承辦人
    """

    __tablename__ = "maintenance_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    related_error_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(
        String(20), default=MaintenanceTaskStatus.PENDING, nullable=False
    )
    estimated_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
