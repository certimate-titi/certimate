"""AI Usage Tracker — Feature 33 成本監控中心.

提供一個 decorator / context manager，讓呼叫 AI API 的地方可以統一記錄
token 用量與成本到 ai_usage_ledger，無需每個 service 手動埋點。

使用範例：

    from app.middleware.ai_usage_tracker import track_ai_usage

    with track_ai_usage(db, provider="anthropic", feature="ai_gen") as tracker:
        response = anthropic_client.messages.create(...)
        tracker.input_tokens = response.usage.input_tokens
        tracker.output_tokens = response.usage.output_tokens
        tracker.cost_usd = estimate_anthropic_cost(
            response.usage.input_tokens,
            response.usage.output_tokens,
            model=response.model,
        )
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import Iterator
import uuid

from sqlalchemy.orm import Session

from app.repositories.ai_usage_repository import AiUsageRepository

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pricing tables (USD per 1M tokens) — adjust as providers change pricing
# ---------------------------------------------------------------------------

_ANTHROPIC_PRICES = {
    # model_id: (input_per_m, output_per_m)
    "claude-opus-4-6":   (Decimal("15.00"), Decimal("75.00")),
    "claude-sonnet-4-6": (Decimal("3.00"),  Decimal("15.00")),
    "claude-haiku-4-5":  (Decimal("0.25"),  Decimal("1.25")),
}

_GEMINI_PRICES = {
    "gemini-2.5-pro":    (Decimal("1.25"),  Decimal("5.00")),
    "gemini-2.5-flash":  (Decimal("0.075"), Decimal("0.30")),
    "text-embedding-004": (Decimal("0.025"), Decimal("0")),
}

_VOYAGE_PRICES = {
    "voyage-3":      Decimal("0.12"),
    "voyage-3-lite": Decimal("0.02"),
}


def estimate_anthropic_cost(
    input_tokens: int, output_tokens: int, model: str = "claude-haiku-4-5"
) -> Decimal:
    prices = _ANTHROPIC_PRICES.get(model, _ANTHROPIC_PRICES["claude-haiku-4-5"])
    return (
        Decimal(input_tokens) * prices[0] / Decimal("1000000")
        + Decimal(output_tokens) * prices[1] / Decimal("1000000")
    )


def estimate_gemini_cost(
    input_tokens: int, output_tokens: int, model: str = "gemini-2.5-flash"
) -> Decimal:
    prices = _GEMINI_PRICES.get(model, _GEMINI_PRICES["gemini-2.5-flash"])
    return (
        Decimal(input_tokens) * prices[0] / Decimal("1000000")
        + Decimal(output_tokens) * prices[1] / Decimal("1000000")
    )


def estimate_voyage_cost(
    input_tokens: int, model: str = "voyage-3"
) -> Decimal:
    price = _VOYAGE_PRICES.get(model, _VOYAGE_PRICES["voyage-3"])
    return Decimal(input_tokens) * price / Decimal("1000000")


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


@dataclass
class _UsageTracker:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Decimal("0")
    endpoint: str | None = None
    request_id: str | None = None


@contextmanager
def track_ai_usage(
    db: Session,
    *,
    provider: str,
    feature: str,
    user_id: uuid.UUID | None = None,
) -> Iterator[_UsageTracker]:
    """Record AI usage once the block exits (even on exception)."""
    tracker = _UsageTracker()
    try:
        yield tracker
    finally:
        try:
            repo = AiUsageRepository(db)
            repo.record(
                provider=provider,
                endpoint=tracker.endpoint,
                input_tokens=tracker.input_tokens,
                output_tokens=tracker.output_tokens,
                cost_usd=tracker.cost_usd,
                feature=feature,
                user_id=user_id,
                request_id=tracker.request_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("ai_usage_ledger record failed: %s", exc)
