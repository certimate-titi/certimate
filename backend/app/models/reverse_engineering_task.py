"""ReverseEngineeringTask ORM Model — derived from erm.dbml."""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class ReverseEngineeringStatus(str, enum.Enum):
    """逆向工程任務狀態列舉。"""

    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReverseEngineeringTask(Base):
    """從題目反向重建知識節點樹的任務紀錄。

    對應 DBML 表：reverse_engineering_tasks

    Attributes:
        subject_id: 對應科目
        triggered_by: 發起使用者
        status: PROCESSING / COMPLETED / FAILED
        total_questions: 用於重建的題數
        node_count: 重建出的節點數
        coverage_rate: 題目覆蓋率（百分比）
        max_depth: 樹深度
        orphan_node_count: 孤兒節點數
        reliability: 可靠度（high / medium / low）
        completed_at: 完成時間
    """

    __tablename__ = "reverse_engineering_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    triggered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(ReverseEngineeringStatus, name="reverse_engineering_status",
             create_type=True,
             values_callable=lambda e: [m.value for m in e]),
        server_default="PROCESSING",
    )
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    node_count: Mapped[int | None] = mapped_column(Integer)
    coverage_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    max_depth: Mapped[int | None] = mapped_column(Integer)
    orphan_node_count: Mapped[int | None] = mapped_column(Integer, default=0)
    reliability: Mapped[str | None] = mapped_column(String(10))
    error_message: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
