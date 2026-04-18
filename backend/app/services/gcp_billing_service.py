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


# Test injection hooks (BDD only)
_TEST_OVERRIDE: dict = {
    "total": None,  # Monthly total override
    "services": None,  # Services list override（from BigQuery table in feature）
    "daily_series": None,  # Daily trend override
}


def set_test_override(total_usd: Decimal | None) -> None:
    """BDD test hook: force GcpBillingService to return a specific monthly total.

    Pass `None` to reset.
    """
    _TEST_OVERRIDE["total"] = total_usd


def set_test_services(services: list[dict] | None) -> None:
    """BDD test hook: inject services list from feature table.

    Expected format:
        [
            {"service_name": "Cloud Run", "cost_usd": 120.00},
            {"service_name": "Cloud SQL", "cost_usd": 180.25},
            ...
        ]
    Pass `None` to reset.
    """
    _TEST_OVERRIDE["services"] = services


def set_test_daily_series(daily_series: list[dict] | None) -> None:
    """BDD test hook: inject daily trend data from feature table.

    Expected format:
        [
            {"billing_date": "2026-04-01", "cost_usd": 15.00},
            ...
        ]
    Pass `None` to reset.
    """
    _TEST_OVERRIDE["daily_series"] = daily_series


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

    # GCP Billing Export 標準表名模板
    # 實際表名通常為 gcp_billing_export_v1_{YYYYMM} 格式
    # 使用通配符 * 查詢當月所有分區
    _DATASET_TABLE_TEMPLATE = "`{project}.{dataset}.{table_prefix}_*`"

    def __init__(
        self,
        project_id: str | None = None,
        dataset: str | None = None,
        table_prefix: str | None = None,
        credentials_path: str | None = None,
    ) -> None:
        from app.core.config import get_settings
        settings = get_settings()

        self.project_id = project_id or settings.GCP_PROJECT_ID
        self.dataset = dataset or settings.GCP_BILLING_EXPORT_DATASET
        self.table_prefix = table_prefix or settings.GCP_BILLING_EXPORT_TABLE
        self.credentials_path = credentials_path or settings.GCP_BQ_CREDENTIALS_PATH
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
        Otherwise → stub data (with optional test_override injections).
        """
        # Real mode
        if os.getenv("GCP_BILLING_MODE", "fake") == "real":
            return self._load_monthly_summary_real(year, month)

        if not self._is_configured():
            logger.warning("GcpBillingService not configured; returning stub data")

        period_start = date(year, month, 1)
        period_end = date.today()

        # 測試 hook #1: 若有注入的 services 列表（來自 feature table），使用它
        injected_services = _TEST_OVERRIDE.get("services")
        if injected_services is not None:
            services = [
                GcpServiceCost(
                    service_name=s.get("service_name") or s.get("service") or "unknown",
                    cost_usd=Decimal(str(s.get("cost_usd") or 0)),
                )
                for s in injected_services
            ]
            total = sum((s.cost_usd for s in services), Decimal("0"))
            return GcpBillingSummary(
                total_usd=total,
                services=services,
                cached_at=datetime.now(timezone.utc),
                period_start=period_start,
                period_end=period_end,
            )

        # 測試 hook #2: 若有注入的 monthly total，使用它
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

        # 默認 stub 資料
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
        """從 BigQuery Billing Export 查詢當月成本彙總（按服務分類）。

        GCP Billing Export 表結構：
        - service.description: 服務名稱（如 "Cloud Run", "Cloud SQL"）
        - cost: 成本金額（float）
        - currency: 貨幣代碼（通常 "USD"）
        - usage_start_time / usage_end_time: 使用時段
        - export_time: 導出時間（分區欄位，TIMESTAMP）
        """
        period_start = date(year, month, 1)
        period_end = date.today()
        table = self._DATASET_TABLE_TEMPLATE.format(
            project=self.project_id,
            dataset=self.dataset,
            table_prefix=self.table_prefix,
        )
        # Billing export costs are in the billing account's local currency
        # (e.g. TWD for TW accounts). currency_conversion_rate is USD -> local,
        # so USD cost = cost / rate. Guard against null/zero rate.
        sql = f"""
        SELECT
          service.description AS service_name,
          ROUND(SUM(SAFE_DIVIDE(cost, currency_conversion_rate)), 2) AS cost_usd
        FROM {table}
        WHERE DATE(export_time) >= DATE('{period_start.isoformat()}')
          AND DATE(export_time) <= DATE('{period_end.isoformat()}')
        GROUP BY service.description
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
        logger.info(
            "GCP Billing Export: loaded %d services for %d-%02d, total: $%.2f",
            len(services),
            year,
            month,
            total,
        )
        return GcpBillingSummary(
            total_usd=total,
            services=services,
            cached_at=datetime.now(timezone.utc),
            period_start=period_start,
            period_end=period_end,
        )

    def _load_daily_trend_real(self, days: int) -> list[GcpDailyCost]:
        """從 BigQuery Billing Export 查詢最近 N 天的每日成本趨勢。"""
        end = date.today()
        start = end - timedelta(days=days)
        table = self._DATASET_TABLE_TEMPLATE.format(
            project=self.project_id,
            dataset=self.dataset,
            table_prefix=self.table_prefix,
        )
        sql = f"""
        SELECT
          DATE(export_time) AS billing_date,
          ROUND(SUM(SAFE_DIVIDE(cost, currency_conversion_rate)), 2) AS cost_usd
        FROM {table}
        WHERE DATE(export_time) >= DATE('{start.isoformat()}')
          AND DATE(export_time) <= DATE('{end.isoformat()}')
        GROUP BY billing_date
        ORDER BY billing_date ASC
        """
        rows = self._run_query(sql)
        logger.info("GCP Billing Export: loaded %d daily records for %d days", len(rows), days)
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
        from app.core.config import get_settings
        settings = get_settings()

        if settings.GCP_BILLING_MODE != "real":
            raise NotImplementedError(
                "GCP_BILLING_MODE!=real; using stub data. Set GCP_BILLING_MODE=real "
                "and pip install google-cloud-bigquery to enable."
            )

        # 檢查必要的配置
        if not self.project_id:
            raise GcpBillingUnavailable("GCP_PROJECT_ID 未設定")
        if not self.dataset:
            raise GcpBillingUnavailable("GCP_BILLING_EXPORT_DATASET 未設定")

        try:
            from google.cloud import bigquery  # type: ignore[import-not-found]
            from google.oauth2 import service_account  # type: ignore[import-not-found]
        except ImportError as exc:
            raise GcpBillingUnavailable(
                f"google-cloud-bigquery 未安裝。請執行：pip install google-cloud-bigquery {exc}"
            )

        if self._bq_client is None:
            try:
                if self.credentials_path:
                    if not os.path.exists(self.credentials_path):
                        raise GcpBillingUnavailable(
                            f"GCP_BQ_CREDENTIALS_PATH 檔案不存在: {self.credentials_path}"
                        )
                    creds = service_account.Credentials.from_service_account_file(
                        self.credentials_path
                    )
                    self._bq_client = bigquery.Client(
                        project=self.project_id, credentials=creds
                    )
                    auth_source = f"file={self.credentials_path}"
                else:
                    # Fall back to Application Default Credentials
                    # (Cloud Run service account / gcloud auth application-default)
                    self._bq_client = bigquery.Client(project=self.project_id)
                    auth_source = "ADC"
                logger.info(
                    "GCP BigQuery client initialized for project %s, dataset %s, auth=%s",
                    self.project_id,
                    self.dataset,
                    auth_source,
                )
            except GcpBillingUnavailable:
                raise
            except Exception as exc:  # noqa: BLE001
                raise GcpBillingUnavailable(
                    f"無法初始化 GCP BigQuery client: {exc}"
                )

        try:
            logger.debug("Executing BigQuery query: %s", sql)
            result = self._bq_client.query(sql).result()
            rows = [dict(row) for row in result]
            logger.debug("BigQuery query returned %d rows", len(rows))
            return rows
        except Exception as exc:  # noqa: BLE001
            logger.error("BigQuery 查詢失敗: %s", exc)
            raise GcpBillingUnavailable(f"BigQuery 查詢失敗: {exc}")

    def _is_configured(self) -> bool:
        """檢查是否已正確配置 GCP Billing Export。"""
        has_project = bool(self.project_id)
        has_dataset = bool(self.dataset)
        has_creds = bool(self.credentials_path) and os.path.exists(self.credentials_path)

        if not (has_project and has_dataset and has_creds):
            logger.debug(
                "GCP Billing not fully configured: project=%s, dataset=%s, creds=%s",
                has_project,
                has_dataset,
                has_creds,
            )
        return has_project and has_dataset and has_creds
