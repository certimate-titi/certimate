"""BudgetAlertLog Repository — Feature 33 成本監控中心."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.budget_alert_log import BudgetAlertLog


class BudgetAlertLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        scope: str,
        alert_type: str,  # WARNING / DEGRADE / DISABLED
        triggered_at_usd: Decimal,
        limit_usd: Decimal,
        percent: Decimal,
        notified_channels: list[str] | None = None,
    ) -> BudgetAlertLog:
        entry = BudgetAlertLog(
            scope=scope,
            alert_type=alert_type,
            triggered_at_usd=triggered_at_usd,
            limit_usd=limit_usd,
            percent=percent,
            notified_channels=notified_channels,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def list_recent(self, scope: str | None = None, limit: int = 50) -> list[BudgetAlertLog]:
        q = self.db.query(BudgetAlertLog)
        if scope:
            q = q.filter(BudgetAlertLog.scope == scope)
        return q.order_by(BudgetAlertLog.created_at.desc()).limit(limit).all()

    def mark_resolved(self, alert_id, resolved_at: datetime) -> None:
        entry = self.db.query(BudgetAlertLog).filter(BudgetAlertLog.id == alert_id).first()
        if entry:
            entry.resolved_at = resolved_at
            self.db.flush()
