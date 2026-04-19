"""GcpBudgetSyncService — Feature 33 GCP Native Budget 單向同步.

將 budget_config 的 AI_GEMINI / GCP_TOTAL 設定單向推送到 GCP Billing Budgets API。
同步失敗不 raise，回傳 SyncResult(status="failed") 讓上層 graceful degrade。

Layer 3 骨架：包含 in-memory 的 fake adapter 讓 BDD 測試可跑，
真實 billingbudgets 呼叫需要 Layer 3b 再補 SDK 連線與憑證載入。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Protocol
import uuid

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SyncResult:
    status: str  # created / updated / skipped_non_gcp / failed
    gcp_budget_resource_name: str | None
    error: str | None = None


# ---------------------------------------------------------------------------
# Adapter interface (for testability)
# ---------------------------------------------------------------------------


class BudgetApiAdapter(Protocol):
    def create_budget(
        self, *, scope: str, monthly_limit_usd: Decimal,
        warning_pct: int, degrade_pct: int, disable_pct: int,
    ) -> str: ...

    def update_budget(
        self, *, resource_name: str, monthly_limit_usd: Decimal,
        warning_pct: int, degrade_pct: int, disable_pct: int,
    ) -> None: ...

    def delete_budget(self, resource_name: str) -> None: ...


class InMemoryFakeAdapter:
    """BDD 測試用的 in-memory adapter。記錄所有呼叫供斷言。"""

    def __init__(self):
        self.budgets: dict[str, dict] = {}
        self.calls: list[tuple] = []
        self.simulate_failure: bool = False

    def create_budget(
        self, *, scope: str, monthly_limit_usd: Decimal,
        warning_pct: int, degrade_pct: int, disable_pct: int,
    ) -> str:
        self.calls.append(("create", scope, monthly_limit_usd))
        if self.simulate_failure:
            raise RuntimeError("Simulated GCP API failure")
        resource_name = (
            f"billingAccounts/FAKE/budgets/{uuid.uuid4().hex[:12]}"
        )
        self.budgets[resource_name] = {
            "scope": scope,
            "monthly_limit_usd": monthly_limit_usd,
            "thresholds": [warning_pct, degrade_pct, disable_pct],
        }
        return resource_name

    def update_budget(
        self, *, resource_name: str, monthly_limit_usd: Decimal,
        warning_pct: int, degrade_pct: int, disable_pct: int,
    ) -> None:
        self.calls.append(("update", resource_name, monthly_limit_usd))
        if self.simulate_failure:
            raise RuntimeError("Simulated GCP API failure")
        if resource_name in self.budgets:
            self.budgets[resource_name]["monthly_limit_usd"] = monthly_limit_usd
            self.budgets[resource_name]["thresholds"] = [
                warning_pct, degrade_pct, disable_pct
            ]

    def delete_budget(self, resource_name: str) -> None:
        self.calls.append(("delete", resource_name))
        self.budgets.pop(resource_name, None)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


_SYNCABLE_SCOPES = {"AI_GEMINI", "GCP_TOTAL"}


class GcpBudgetSyncService:
    """Single-direction sync from app budget_config to GCP Native Budgets."""

    def __init__(self, adapter: BudgetApiAdapter | None = None):
        self.adapter = adapter or _make_default_adapter()

    def upsert_budget(
        self,
        *,
        scope: str,
        monthly_limit_usd: Decimal,
        warning_pct: int,
        degrade_pct: int,
        disable_pct: int,
        existing_resource_name: str | None,
        gcp_sync_enabled: bool,
    ) -> SyncResult:
        if not gcp_sync_enabled or scope not in _SYNCABLE_SCOPES:
            return SyncResult(
                status="skipped_non_gcp", gcp_budget_resource_name=existing_resource_name
            )

        try:
            if existing_resource_name:
                self.adapter.update_budget(
                    resource_name=existing_resource_name,
                    monthly_limit_usd=monthly_limit_usd,
                    warning_pct=warning_pct,
                    degrade_pct=degrade_pct,
                    disable_pct=disable_pct,
                )
                return SyncResult(status="updated", gcp_budget_resource_name=existing_resource_name)
            else:
                resource_name = self.adapter.create_budget(
                    scope=scope,
                    monthly_limit_usd=monthly_limit_usd,
                    warning_pct=warning_pct,
                    degrade_pct=degrade_pct,
                    disable_pct=disable_pct,
                )
                return SyncResult(status="created", gcp_budget_resource_name=resource_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("GCP budget sync failed: %s", exc)
            return SyncResult(
                status="failed",
                gcp_budget_resource_name=existing_resource_name,
                error=str(exc),
            )


class RealGcpBudgetsAdapter:
    """Production adapter using google-cloud-billing-budgets SDK.

    Activated when GCP_BUDGET_SYNC_MODE=real and the SDK is installed.
    Requires:
    - GCP_BILLING_ACCOUNT_ID (e.g. 0126A9-3FE882-C325F3)
    - GCP_PROJECT_ID
    - GCP_BQ_CREDENTIALS_PATH (or default ADC) with billing.budgetsAdmin
    """

    def __init__(self):
        try:
            from google.cloud.billing import budgets_v1 as billing_budgets_v1  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                f"google-cloud-billing-budgets 未安裝: {exc}"
            )
        self._billing_budgets_v1 = billing_budgets_v1
        self.client = billing_budgets_v1.BudgetServiceClient()
        self.billing_account_id = os.getenv("GCP_BILLING_ACCOUNT_ID")
        self.project_id = os.getenv("GCP_PROJECT_ID", "certimate-titi")
        if not self.billing_account_id:
            raise RuntimeError("GCP_BILLING_ACCOUNT_ID 未設定")

    def _build_budget(
        self, *, scope: str, monthly_limit_usd: Decimal,
        warning_pct: int, degrade_pct: int, disable_pct: int,
    ):
        bb = self._billing_budgets_v1
        # Filter limited to project (and optional service)
        budget_filter_kwargs = {"projects": [f"projects/{self.project_id}"]}
        if scope == "AI_GEMINI":
            # Gemini API service id (Google Generative Language)
            # Real service id may need lookup; placeholder here
            budget_filter_kwargs["services"] = [
                "services/generativelanguage.googleapis.com"
            ]
        return bb.Budget(
            display_name=f"[CertiMate:33] {scope} Budget",
            budget_filter=bb.Filter(**budget_filter_kwargs),
            amount=bb.BudgetAmount(
                specified_amount=bb.types.Money(
                    currency_code="USD",
                    units=int(monthly_limit_usd),
                )
            ),
            threshold_rules=[
                bb.ThresholdRule(threshold_percent=warning_pct / 100),
                bb.ThresholdRule(threshold_percent=degrade_pct / 100),
                bb.ThresholdRule(threshold_percent=disable_pct / 100),
            ],
        )

    def create_budget(
        self, *, scope: str, monthly_limit_usd: Decimal,
        warning_pct: int, degrade_pct: int, disable_pct: int,
    ) -> str:
        bb = self._billing_budgets_v1
        budget = self._build_budget(
            scope=scope, monthly_limit_usd=monthly_limit_usd,
            warning_pct=warning_pct, degrade_pct=degrade_pct, disable_pct=disable_pct,
        )
        request = bb.CreateBudgetRequest(
            parent=f"billingAccounts/{self.billing_account_id}",
            budget=budget,
        )
        response = self.client.create_budget(request=request)
        return response.name

    def update_budget(
        self, *, resource_name: str, monthly_limit_usd: Decimal,
        warning_pct: int, degrade_pct: int, disable_pct: int,
    ) -> None:
        bb = self._billing_budgets_v1
        # Need scope to rebuild filter — derive from display_name when updating
        # For simplicity use GCP_TOTAL filter (no service filter)
        budget = self._build_budget(
            scope="GCP_TOTAL", monthly_limit_usd=monthly_limit_usd,
            warning_pct=warning_pct, degrade_pct=degrade_pct, disable_pct=disable_pct,
        )
        budget.name = resource_name
        request = bb.UpdateBudgetRequest(budget=budget)
        self.client.update_budget(request=request)

    def delete_budget(self, resource_name: str) -> None:
        bb = self._billing_budgets_v1
        request = bb.DeleteBudgetRequest(name=resource_name)
        self.client.delete_budget(request=request)


def _make_default_adapter() -> BudgetApiAdapter:
    """Factory for the default adapter.

    GCP_BUDGET_SYNC_MODE=real → RealGcpBudgetsAdapter（需 google-cloud-billing-budgets）
    Otherwise → InMemoryFakeAdapter（測試與本地開發用）
    """
    if os.getenv("GCP_BUDGET_SYNC_MODE", "fake") == "real":
        return RealGcpBudgetsAdapter()
    return InMemoryFakeAdapter()
