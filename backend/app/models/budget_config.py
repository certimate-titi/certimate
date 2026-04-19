"""BudgetConfig ORM Model — derived from erm.dbml budget_config table.

Feature 33 — 成本監控中心
預算設定與當前狀態，supports 4 scopes: AI_ANTHROPIC / AI_GEMINI / AI_VOYAGE / GCP_TOTAL.
"""

from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class BudgetConfig(Base):
    __tablename__ = "budget_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scope: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    monthly_limit_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    warning_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    degrade_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    disable_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    current_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active"
    )
    overridden_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Feature 33 — GCP Native Budget 單向同步
    gcp_budget_resource_name: Mapped[str | None] = mapped_column(String(256))
    gcp_sync_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    gcp_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
