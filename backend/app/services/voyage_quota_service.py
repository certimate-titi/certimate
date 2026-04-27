"""VoyageQuotaService — Feature 33 Voyage 配額鎖與降級佇列

呼叫 Voyage Embedding API 之前必須先經過 check_and_reserve 檢查。
達 80% 降級門檻時，新資源會被標記為 PENDING_BUDGET_RECOVERY 不進入 Voyage。
達 100% 時硬性拒絕。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.ai_usage_repository import AiUsageRepository
from app.repositories.budget_config_repository import BudgetConfigRepository


class VoyageQuotaExceeded(Exception):
    """Raised when current_usage + estimated_cost exceeds the disable threshold."""


class VoyageQuotaDegraded(Exception):
    """Raised when current_usage has reached the degrade threshold.

    Caller should mark the target resource as PENDING_BUDGET_RECOVERY
    rather than calling Voyage.
    """


@dataclass(frozen=True)
class QuotaCheckResult:
    """Quota Check Result。"""
    allowed: bool
    current_usd: Decimal
    limit_usd: Decimal
    percent: Decimal
    state: str  # active / warning / degraded / disabled


class VoyageQuotaService:
    """Voyage Quota Service 服務類別。"""
    SCOPE = "AI_VOYAGE"

    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db
        self.ledger_repo = AiUsageRepository(db)
        self.budget_repo = BudgetConfigRepository(db)

    def check_and_reserve(self, estimated_cost_usd: Decimal) -> QuotaCheckResult:
        """Check current usage and decide whether the Voyage call is allowed.

        Behavior:
        - current + estimated <= warning*limit  → allowed, state=active
        - <= degrade*limit                      → allowed, state=warning
        - < disable*limit                       → raise VoyageQuotaDegraded
        - >= disable*limit                      → raise VoyageQuotaExceeded
        """
        config = self.budget_repo.get_by_scope(self.SCOPE)
        if config is None:
            # Budget not configured; default to allow (fail-open, but log)
            return QuotaCheckResult(True, Decimal("0"), Decimal("0"), Decimal("0"), "active")

        now = datetime.now(timezone.utc)
        current_usd, _, _ = self.ledger_repo.sum_month(
            provider="voyage", year=now.year, month=now.month
        )
        projected = current_usd + estimated_cost_usd
        limit = Decimal(config.monthly_limit_usd)
        percent = (projected / limit * Decimal("100")) if limit > 0 else Decimal("0")

        warn_usd = limit * Decimal(config.warning_percent) / Decimal("100")
        degrade_usd = limit * Decimal(config.degrade_percent) / Decimal("100")
        disable_usd = limit * Decimal(config.disable_percent) / Decimal("100")

        if projected >= disable_usd:
            raise VoyageQuotaExceeded(
                f"AI_VOYAGE quota exceeded: projected={projected} limit={limit}"
            )
        if projected >= degrade_usd:
            raise VoyageQuotaDegraded(
                f"AI_VOYAGE quota degraded: projected={projected} limit={limit}"
            )

        state = "warning" if projected >= warn_usd else "active"
        return QuotaCheckResult(True, current_usd, limit, percent, state)
