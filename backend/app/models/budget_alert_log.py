"""BudgetAlertLog ORM Model — derived from erm.dbml budget_alert_log table.

Feature 33 — 成本監控中心
預算告警歷史紀錄（WARNING / DEGRADE / DISABLED 三級）。
"""

from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class BudgetAlertLog(Base):
    __tablename__ = "budget_alert_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(16), nullable=False)
    triggered_at_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    limit_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    notified_channels: Mapped[list | None] = mapped_column(JSONB)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
