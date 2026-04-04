"""EarlyWarningRule ORM Model — derived from erm.dbml."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class EarlyWarningRule(Base):
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
