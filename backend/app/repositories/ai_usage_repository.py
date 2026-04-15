"""AiUsageLedger Repository — Feature 33 成本監控中心."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ai_usage_ledger import AiUsageLedger


class AiUsageRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        provider: str,
        endpoint: str | None,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal,
        feature: str | None,
        user_id: uuid.UUID | None = None,
        request_id: str | None = None,
        billing_source: str = "app",
    ) -> AiUsageLedger:
        entry = AiUsageLedger(
            provider=provider,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            feature=feature,
            user_id=user_id,
            request_id=request_id,
            billing_source=billing_source,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def sum_month(
        self, provider: str, year: int, month: int
    ) -> tuple[Decimal, int, int]:
        """Return (total_cost_usd, input_tokens, output_tokens) for the given month."""
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            if month == 12
            else datetime(year, month + 1, 1, tzinfo=timezone.utc)
        )
        row = (
            self.db.query(
                func.coalesce(func.sum(AiUsageLedger.cost_usd), 0),
                func.coalesce(func.sum(AiUsageLedger.input_tokens), 0),
                func.coalesce(func.sum(AiUsageLedger.output_tokens), 0),
            )
            .filter(AiUsageLedger.provider == provider)
            .filter(AiUsageLedger.created_at >= start)
            .filter(AiUsageLedger.created_at < end)
            .one()
        )
        return Decimal(str(row[0])), int(row[1]), int(row[2])

    def daily_series(
        self, provider: str | None, days: int
    ) -> list[tuple[datetime, Decimal]]:
        """Return [(date, cost_usd), ...] for the last N days."""
        q = self.db.query(
            func.date_trunc("day", AiUsageLedger.created_at).label("day"),
            func.coalesce(func.sum(AiUsageLedger.cost_usd), 0).label("cost"),
        )
        if provider:
            q = q.filter(AiUsageLedger.provider == provider)
        q = q.group_by("day").order_by("day")
        return [(row.day, Decimal(str(row.cost))) for row in q.limit(days)]

    def month_total_all_providers(
        self, year: int, month: int
    ) -> dict[str, Decimal]:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            if month == 12
            else datetime(year, month + 1, 1, tzinfo=timezone.utc)
        )
        rows = (
            self.db.query(
                AiUsageLedger.provider,
                func.coalesce(func.sum(AiUsageLedger.cost_usd), 0),
            )
            .filter(AiUsageLedger.created_at >= start)
            .filter(AiUsageLedger.created_at < end)
            .group_by(AiUsageLedger.provider)
            .all()
        )
        return {row[0]: Decimal(str(row[1])) for row in rows}
