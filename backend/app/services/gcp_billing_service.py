"""GCP Billing Service — Feature 33 成本監控中心

封裝 BigQuery Billing Export 查詢，提供：
- 當月總計（by service）
- 30 天趨勢
- 單一服務明細

查詢結果快取 1 小時，避免 BQ 查詢費用累積。
若憑證或連線失敗，回傳 503 語意讓 Router 層降級。

Layer 2 僅提供介面與假資料實作，真實 BigQuery 連線由 Layer 3 後端工程師完成。
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GcpServiceCost:
    service_name: str
    cost_usd: Decimal
    currency: str = "USD"


@dataclass(frozen=True)
class GcpDailyCost:
    billing_date: date
    cost_usd: Decimal


@dataclass(frozen=True)
class GcpBillingSummary:
    total_usd: Decimal
    services: list[GcpServiceCost]
    cached_at: datetime
    period_start: date
    period_end: date


class GcpBillingUnavailable(Exception):
    """Raised when BigQuery billing export is unreachable or misconfigured.

    Router 層應捕捉此例外並回傳 503 + code `GCP_BILLING_TEMPORARILY_UNAVAILABLE`。
    """


# Test injection hook (BDD only) — see `set_test_override` below.
_TEST_OVERRIDE: dict = {"total": None}


def set_test_override(total_usd: Decimal | None) -> None:
    """BDD test hook: force GcpBillingService to return a specific monthly total.

    Pass `None` to reset.
    """
    _TEST_OVERRIDE["total"] = total_usd


# ---------------------------------------------------------------------------
# Simple TTL cache (避免引入額外依賴)
# ---------------------------------------------------------------------------


class _TTLCache:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, object]] = {}

    def get_or_set(self, key: str, loader: Callable[[], object]) -> object:
        now = time.monotonic()
        entry = self._store.get(key)
        if entry and (now - entry[0]) < self._ttl:
            return entry[1]
        value = loader()
        self._store[key] = (now, value)
        return value

    def invalidate(self, key: str | None = None) -> None:
        if key is None:
            self._store.clear()
        else:
            self._store.pop(key, None)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class GcpBillingService:
    """BigQuery Billing Export 查詢服務（介面層）。

    Layer 3 實作時需要：
    1. 讀取 `GCP_BQ_CREDENTIALS_PATH` 環境變數並以 google-cloud-bigquery 連線
    2. 實作 `_run_query()` 執行真正的 BQ SQL 查詢
    3. 失敗時 raise GcpBillingUnavailable
    4. 將本檔案的 stub 方法替換為真實查詢
    """

    _DATASET_TABLE_TEMPLATE = (
        "`{project}.{dataset}.gcp_billing_export_v1_*`"
    )

    def __init__(
        self,
        project_id: str | None = None,
        dataset: str | None = None,
        credentials_path: str | None = None,
    ) -> None:
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.dataset = dataset or os.getenv(
            "GCP_BILLING_EXPORT_DATASET", "billing_export"
        )
        self.credentials_path = credentials_path or os.getenv(
            "GCP_BQ_CREDENTIALS_PATH"
        )
        self._cache = _TTLCache(ttl_seconds=3600)
        self._bq_client = None  # Layer 3 填入 google.cloud.bigquery.Client

    # -- Public API ---------------------------------------------------------

    def get_monthly_summary(self, year: int, month: int) -> GcpBillingSummary:
        """當月所有服務成本彙總（依金額降冪）。"""
        cache_key = f"summary:{year}-{month:02d}"
        return self._cache.get_or_set(
            cache_key, lambda: self._load_monthly_summary(year, month)
        )  # type: ignore[return-value]

    def get_daily_trend(self, days: int = 30) -> list[GcpDailyCost]:
        """最近 N 天的每日總成本。"""
        cache_key = f"trend:{days}"
        return self._cache.get_or_set(
            cache_key, lambda: self._load_daily_trend(days)
        )  # type: ignore[return-value]

    def invalidate_cache(self) -> None:
        """Super Admin 手動刷新或測試用。"""
        self._cache.invalidate()

    # -- Private (Layer 3 覆寫點) -------------------------------------------

    def _load_monthly_summary(self, year: int, month: int) -> GcpBillingSummary:
        """Load monthly cost summary.

        Real mode (GCP_BILLING_MODE=real) → BigQuery billing_export query.
        Otherwise → stub data (with optional set_test_override).
        """
        # Real mode
        if os.getenv("GCP_BILLING_MODE", "fake") == "real":
            return self._load_monthly_summary_real(year, month)

        if not self._is_configured():
            logger.warning("GcpBillingService not configured; returning stub data")

        period_start = date(year, month, 1)
        period_end = date.today()

        # 測試 hook
        override_total = _TEST_OVERRIDE.get("total")
        if override_total is not None:
            services = [GcpServiceCost("TEST_OVERRIDE", override_total)]
            return GcpBillingSummary(
                total_usd=override_total,
                services=services,
                cached_at=datetime.now(timezone.utc),
                period_start=period_start,
                period_end=period_end,
            )

        services = [
            GcpServiceCost("Cloud SQL", Decimal("180.25")),
            GcpServiceCost("Cloud Run", Decimal("120.00")),
            GcpServiceCost("Gemini API", Decimal("85.20")),
            GcpServiceCost("Firebase Hosting", Decimal("25.50")),
            GcpServiceCost("Logging", Decimal("25.00")),
            GcpServiceCost("Cloud Storage", Decimal("15.00")),
        ]
        total = sum((s.cost_usd for s in services), Decimal("0"))

        return GcpBillingSummary(
            total_usd=total,
            services=services,
            cached_at=datetime.now(timezone.utc),
            period_start=period_start,
            period_end=period_end,
        )

    def _load_daily_trend(self, days: int) -> list[GcpDailyCost]:
        """Load daily cost series. Real mode → BigQuery; otherwise → stub."""
        if os.getenv("GCP_BILLING_MODE", "fake") == "real":
            return self._load_daily_trend_real(days)
        today = date.today()
        daily_avg = Decimal("15.00")
        return [
            GcpDailyCost(today - timedelta(days=i), daily_avg)
            for i in range(days)
        ][::-1]

    # ------------------------------------------------------------------
    # Real BigQuery implementations (Layer 3b)
    # ------------------------------------------------------------------

    def _load_monthly_summary_real(self, year: int, month: int) -> GcpBillingSummary:
        period_start = date(year, month, 1)
        period_end = date.today()
        table = self._DATASET_TABLE_TEMPLATE.format(
            project=self.project_id, dataset=self.dataset
        )
        sql = f"""
        SELECT
          service.description AS service_name,
          SUM(cost) AS cost_usd
        FROM {table}
        WHERE DATE(_PARTITIONTIME) >= DATE('{period_start.isoformat()}')
          AND DATE(_PARTITIONTIME) <= DATE('{period_end.isoformat()}')
          AND currency = 'USD'
        GROUP BY service_name
        ORDER BY cost_usd DESC
        """
        rows = self._run_query(sql)
        services = [
            GcpServiceCost(
                service_name=row.get("service_name") or "(unknown)",
                cost_usd=Decimal(str(row.get("cost_usd") or 0)),
            )
            for row in rows
        ]
        total = sum((s.cost_usd for s in services), Decimal("0"))
        return GcpBillingSummary(
            total_usd=total,
            services=services,
            cached_at=datetime.now(timezone.utc),
            period_start=period_start,
            period_end=period_end,
        )

    def _load_daily_trend_real(self, days: int) -> list[GcpDailyCost]:
        end = date.today()
        start = end - timedelta(days=days)
        table = self._DATASET_TABLE_TEMPLATE.format(
            project=self.project_id, dataset=self.dataset
        )
        sql = f"""
        SELECT
          DATE(_PARTITIONTIME) AS billing_date,
          SUM(cost) AS cost_usd
        FROM {table}
        WHERE DATE(_PARTITIONTIME) >= DATE('{start.isoformat()}')
          AND DATE(_PARTITIONTIME) <= DATE('{end.isoformat()}')
          AND currency = 'USD'
        GROUP BY billing_date
        ORDER BY billing_date
        """
        rows = self._run_query(sql)
        return [
            GcpDailyCost(
                billing_date=row.get("billing_date") or end,
                cost_usd=Decimal(str(row.get("cost_usd") or 0)),
            )
            for row in rows
        ]

    def _run_query(self, sql: str) -> list[dict]:
        """Execute a BigQuery SQL query against the billing_export dataset.

        Activated when GCP_BILLING_MODE=real and google-cloud-bigquery is installed.
        Layer 3b 真實實作。
        """
        if os.getenv("GCP_BILLING_MODE", "fake") != "real":
            raise NotImplementedError(
                "GCP_BILLING_MODE!=real; using stub data. Set GCP_BILLING_MODE=real "
                "and pip install google-cloud-bigquery to enable."
            )
        try:
            from google.cloud import bigquery  # type: ignore[import-not-found]
            from google.oauth2 import service_account  # type: ignore[import-not-found]
        except ImportError as exc:
            raise GcpBillingUnavailable(
                f"google-cloud-bigquery 未安裝: {exc}"
            )

        if self._bq_client is None:
            if not self.credentials_path or not os.path.exists(self.credentials_path):
                raise GcpBillingUnavailable(
                    "GCP_BQ_CREDENTIALS_PATH 未設定或檔案不存在"
                )
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self._bq_client = bigquery.Client(
                project=self.project_id, credentials=creds
            )

        try:
            return [dict(row) for row in self._bq_client.query(sql).result()]
        except Exception as exc:  # noqa: BLE001
            raise GcpBillingUnavailable(f"BigQuery 查詢失敗: {exc}")

    def _is_configured(self) -> bool:
        return bool(
            self.project_id and self.dataset and self.credentials_path
            and os.path.exists(self.credentials_path)
        )
