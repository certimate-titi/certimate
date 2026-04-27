"""InstitutionAssignment ORM Model — derived from erm.dbml."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class AssignmentStatus(str, enum.Enum):
    """機構派題作業狀態列舉。"""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InstitutionAssignment(Base):
    """B2B 機構派題作業（指定 group 完成考試）。

    對應 DBML 表：institution_assignments

    Attributes:
        institution_id: 所屬機構
        group_id: 接受指派的學生群組
        created_by: 派題者（教師/管理員）
        exam_config: JSONB，包含科目、題數、難度等出題參數
        deadline: 截止時間（NULL = 無期限）
        status: pending / active / completed / cancelled
    """

    __tablename__ = "institution_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
        nullable=False,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_groups.id"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    exam_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=AssignmentStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
