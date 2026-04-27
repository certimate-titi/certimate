"""EarlyWarningRule ORM Model — derived from erm.dbml."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class EarlyWarningRule(Base):
    """B2B 機構早期預警規則設定。

    對應 DBML 表：early_warning_rules
    每個 institution 一筆（institution_id unique）。

    Attributes:
        institution_id: 機構 id（unique，CASCADE 刪除）
        min_avg_score: 平均分低於此值觸發預警（預設 60）
        max_decline_trend: 連續下降次數上限（預設 3）
        max_inactive_days: 最長未活躍天數（預設 5）
    """

    __tablename__ = "early_warning_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    min_avg_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=60
    )
    max_decline_trend: Mapped[int] = mapped_column(Integer, default=3)
    max_inactive_days: Mapped[int] = mapped_column(Integer, default=5)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
