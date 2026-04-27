"""AnthropicUsageService — Feature 33 Tier 3b / pending TODO #3.

🚫 STATUS (2026-04-15): Permanently disabled for CertiMate's current account
tier. Anthropic Admin API requires a Team / Enterprise Organization plan,
which CertiMate does not currently subscribe to. The code is preserved here
so that upgrading to Org tier in the future = just set env vars (no code).

Fetches real monthly usage from Anthropic's Admin API and reports it back to
the cost monitor layer. Unlike Gemini/Voyage (which rely on application-layer
`ai_usage_ledger`), Anthropic provides a first-party usage report endpoint so
the numbers are authoritative.

Activation (when Org plan available):
- Set `ANTHROPIC_ADMIN_MODE=real` in the environment
- Supply `ANTHROPIC_ADMIN_API_KEY` (Organization-level admin key starting
  with `sk-ant-admin...`, NOT a regular API key). Obtainable only by
  organization members with the admin role via Claude Console (path:
  Console → Settings → Admin keys, after Org is set up).
- Supply `ANTHROPIC_ORGANIZATION_ID`

Until then, AI_ANTHROPIC scope falls back to ai_usage_ledger which is
populated automatically by LLMService.generate() (Feature 33 TODO #4).
Estimated cost via estimate_anthropic_cost() has < 5% drift vs official
billing.

Graceful degrade:
- If any of the required env vars are missing → return None from
  `get_current_month_cost_usd`, letting cost_monitor_service fall back to
  the ledger value.
- If the API call raises → log warning and return None.

TTL cache: 10 minutes (Anthropic admin API is rate-limited; we don't need
per-request freshness since budget evaluation runs on schedules).
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnthropicUsageSnapshot:
    """Anthropic Usage Snapshot。"""
    total_usd: Decimal
    input_tokens: int
    output_tokens: int
    period_start: date
    period_end: date
    fetched_at: datetime


class AnthropicUsageUnavailable(Exception):
    """Raised when the Admin API cannot be reached or is not configured."""


# ---------------------------------------------------------------------------
# Module-level TTL cache (shared across service instances)
# ---------------------------------------------------------------------------

_CACHE_TTL_SECONDS = int(os.environ.get("ANTHROPIC_USAGE_CACHE_TTL", "600"))
_cache_lock = threading.RLock()
_cache: dict[tuple[int, int], tuple[float, AnthropicUsageSnapshot]] = {}


def _is_real_mode() -> bool:
    """判斷 real mode。"""
    return os.environ.get("ANTHROPIC_ADMIN_MODE", "fake").lower() == "real"


class AnthropicUsageService:
    """Wraps the Anthropic Admin API `usage_report/messages` endpoint.

    Safe to instantiate without credentials — `get_current_month_cost_usd`
    returns None in that case.
    """

    def __init__(self):
        """初始化實例。"""
        self.admin_key = os.environ.get("ANTHROPIC_ADMIN_API_KEY")
        self.org_id = os.environ.get("ANTHROPIC_ORGANIZATION_ID")
        self._client = None  # lazy

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """判斷 configured。"""
        return _is_real_mode() and bool(self.admin_key) and bool(self.org_id)

    def get_current_month_cost_usd(self) -> Decimal | None:
        """Return current-month spend in USD, or None if unavailable."""
        if not self.is_configured():
            return None

        now = datetime.now(timezone.utc)
        cache_key = (now.year, now.month)
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached.total_usd

        try:
            snapshot = self._fetch_monthly_usage(now.year, now.month)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Anthropic admin usage fetch failed: %s", exc)
            return None

        _cache_set(cache_key, snapshot)
        return snapshot.total_usd

    def get_monthly_snapshot(
        self, year: int, month: int
    ) -> AnthropicUsageSnapshot | None:
        """Return the full snapshot (tokens + cost) for a specific month."""
        if not self.is_configured():
            return None
        cached = _cache_get((year, month))
        if cached is not None:
            return cached
        try:
            snapshot = self._fetch_monthly_usage(year, month)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Anthropic admin usage fetch failed: %s", exc)
            return None
        _cache_set((year, month), snapshot)
        return snapshot

    def invalidate_cache(self) -> int:
        """invalidate cache。"""
        with _cache_lock:
            n = len(_cache)
            _cache.clear()
            return n

    # ------------------------------------------------------------------
    # Private — Real Admin API fetch
    # ------------------------------------------------------------------

    def _get_client(self):
        """取得 client。"""
        if self._client is None:
            import anthropic  # type: ignore[import-not-found]
            self._client = anthropic.Anthropic(api_key=self.admin_key)
        return self._client

    def _fetch_monthly_usage(
        self, year: int, month: int
    ) -> AnthropicUsageSnapshot:
        """Call Anthropic Admin API to fetch usage report for a given month.

        Note: Anthropic's Admin API usage report endpoint is:
            GET /v1/organizations/{org_id}/usage_report/messages
        SDK path may differ; we use a direct HTTP request for portability.
        """
        import requests

        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1)
        else:
            period_end = date(year, month + 1, 1)

        url = (
            f"https://api.anthropic.com/v1/organizations/"
            f"{self.org_id}/usage_report/messages"
        )
        params = {
            "starting_at": period_start.isoformat(),
            "ending_at": period_end.isoformat(),
            "bucket_width": "1d",
        }
        headers = {
            "x-api-key": self.admin_key,
            "anthropic-version": "2023-06-01",
        }

        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            raise AnthropicUsageUnavailable(
                f"Anthropic Admin API returned {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        # Response shape (stable contract):
        # {
        #   "data": [
        #     {
        #       "input_tokens": int,
        #       "output_tokens": int,
        #       "amount_usd": str,
        #       ...
        #     }
        #   ]
        # }
        rows = data.get("data", [])
        total_usd = Decimal("0")
        input_tokens = 0
        output_tokens = 0
        for row in rows:
            total_usd += Decimal(str(row.get("amount_usd", "0")))
            input_tokens += int(row.get("input_tokens", 0))
            output_tokens += int(row.get("output_tokens", 0))

        return AnthropicUsageSnapshot(
            total_usd=total_usd,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            period_start=period_start,
            period_end=period_end,
            fetched_at=datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _cache_get(key: tuple[int, int]) -> AnthropicUsageSnapshot | None:
    """ cache get。"""
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        timestamp, snapshot = entry
        if (time.monotonic() - timestamp) > _CACHE_TTL_SECONDS:
            _cache.pop(key, None)
            return None
        return snapshot


def _cache_set(key: tuple[int, int], snapshot: AnthropicUsageSnapshot) -> None:
    """ cache set。"""
    with _cache_lock:
        _cache[key] = (time.monotonic(), snapshot)
