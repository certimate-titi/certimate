"""CostMonitorService — Feature 33 成本監控中心主服務.

整合三家 AI 供應商與 GCP 的成本資料，提供：
- 當月總覽（四個 scope）
- 供應商詳情（token 級明細 + 趨勢）
- GCP 服務分類
- 成本趨勢圖
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.ai_usage_repository import AiUsageRepository
from app.repositories.budget_config_repository import BudgetConfigRepository
from app.services.base import BaseService
from app.services.gcp_billing_service import GcpBillingService, GcpBillingUnavailable


_PROVIDER_TO_SCOPE = {
    "anthropic": "AI_ANTHROPIC",
    "gemini": "AI_GEMINI",
    "voyage": "AI_VOYAGE",
}


class CostMonitorService(BaseService):
    def __init__(self, db: Session, gcp_billing: GcpBillingService | None = None):
        super().__init__(db)
        self.ledger_repo = AiUsageRepository(db)
        self.budget_repo = BudgetConfigRepository(db)
        self.gcp = gcp_billing or GcpBillingService()

    # ------------------------------------------------------------------
    # 當月總覽
    # ------------------------------------------------------------------

    def get_summary(self) -> dict:
        now = datetime.now(timezone.utc)
        configs = {c.scope: c for c in self.budget_repo.list_all()}
        provider_costs = self.ledger_repo.month_total_all_providers(now.year, now.month)

        # Try Anthropic Admin API (TODO #3 — real usage reporting)
        anthropic_authoritative = self._safe_anthropic_cost(now)

        scopes: list[dict] = []
        for scope in ("AI_ANTHROPIC", "AI_GEMINI", "AI_VOYAGE", "GCP_TOTAL"):
            config = configs.get(scope)
            limit = Decimal(config.monthly_limit_usd) if config else Decimal("0")

            if scope == "GCP_TOTAL":
                current = self._safe_gcp_total(now)
            elif scope == "AI_ANTHROPIC" and anthropic_authoritative is not None:
                # Prefer Admin API authoritative value; fallback to ledger
                current = anthropic_authoritative
            else:
                provider_key = scope.removeprefix("AI_").lower()
                current = provider_costs.get(provider_key, Decimal("0"))

            percent = (current / limit * Decimal("100")) if limit > 0 else Decimal("0")
            scopes.append({
                "scope": scope,
                "current_usd": float(round(current, 2)),
                "limit_usd": float(round(limit, 2)),
                "percent": float(round(percent, 2)),
                "state": config.current_state if config else "active",
            })

        return self.ok({"scopes": scopes, "as_of": now.isoformat()})

    def _safe_anthropic_cost(self, now: datetime) -> Decimal | None:
        """Try fetching current-month cost from Anthropic Admin API.

        Returns None if Admin API not configured, rate-limited, or failed.
        In that case caller falls back to ai_usage_ledger.
        """
        try:
            from app.services.anthropic_usage_service import AnthropicUsageService
            return AnthropicUsageService().get_current_month_cost_usd()
        except Exception:  # noqa: BLE001
            return None

    def _safe_gcp_total(self, now: datetime) -> Decimal:
        try:
            summary = self.gcp.get_monthly_summary(now.year, now.month)
            return summary.total_usd
        except GcpBillingUnavailable:
            return Decimal("0")
        except NotImplementedError:
            # Layer 3b 尚未實作真實 BQ 連線；以應用層追蹤的 gemini 成本代替
            return Decimal("0")

    # ------------------------------------------------------------------
    # 單一供應商詳情
    # ------------------------------------------------------------------

    def get_provider_detail(self, provider: str) -> dict:
        provider = provider.lower()
        if provider not in _PROVIDER_TO_SCOPE:
            return self.error(f"unknown provider: {provider}", 400)

        now = datetime.now(timezone.utc)
        cost, input_tokens, output_tokens = self.ledger_repo.sum_month(
            provider, now.year, now.month
        )
        scope = _PROVIDER_TO_SCOPE[provider]
        config = self.budget_repo.get_by_scope(scope)
        limit = Decimal(config.monthly_limit_usd) if config else Decimal("0")

        series = self.ledger_repo.daily_series(provider, days=30)
        daily_series = [
            {"date": day.date().isoformat(), "cost_usd": float(round(cost, 6))}
            for day, cost in series
        ]

        result: dict = {
            "provider": provider,
            "scope": scope,
            "input_tokens_total": input_tokens,
            "output_tokens_total": output_tokens,
            "cost_usd": float(round(cost, 6)),
            "limit_usd": float(round(limit, 2)),
            "daily_series": daily_series,
        }
        if provider == "voyage":
            result["quota_lock_enabled"] = True
            result["quota_remaining_usd"] = float(round(max(limit - cost, Decimal("0")), 2))
        return self.ok(result)

    # ------------------------------------------------------------------
    # GCP 服務分類
    # ------------------------------------------------------------------

    def get_gcp_services(self) -> dict:
        now = datetime.now(timezone.utc)
        try:
            summary = self.gcp.get_monthly_summary(now.year, now.month)
        except GcpBillingUnavailable as exc:
            return {
                "error": True,
                "status_code": 503,
                "code": "GCP_BILLING_TEMPORARILY_UNAVAILABLE",
                "message": f"GCP billing 暫時無法取得: {exc}",
            }
        except NotImplementedError:
            return {
                "error": True,
                "status_code": 503,
                "code": "GCP_BILLING_NOT_CONFIGURED",
                "message": "GCP billing 整合尚未完成",
            }

        services_sorted = sorted(
            summary.services, key=lambda s: s.cost_usd, reverse=True
        )
        return self.ok({
            "total_usd": float(round(summary.total_usd, 2)),
            "services": [
                {
                    "service_name": s.service_name,
                    "cost_usd": float(round(s.cost_usd, 2)),
                }
                for s in services_sorted
            ],
            "cached_at": summary.cached_at.isoformat(),
            "period_start": summary.period_start.isoformat(),
            "period_end": summary.period_end.isoformat(),
        })

    # ------------------------------------------------------------------
    # 成本趨勢（30 天）
    # ------------------------------------------------------------------

    def get_trends(self, days: int = 30) -> dict:
        now = datetime.now(timezone.utc)
        result: dict[str, dict[str, float]] = {}

        # 累積 AI 供應商每日資料
        for provider in ("anthropic", "gemini", "voyage"):
            series = self.ledger_repo.daily_series(provider, days=days)
            for day, cost in series:
                key = day.date().isoformat()
                result.setdefault(key, {
                    "ai_anthropic": 0.0,
                    "ai_gemini": 0.0,
                    "ai_voyage": 0.0,
                    "gcp_total": 0.0,
                })
                result[key][f"ai_{provider}"] = float(round(cost, 6))

        # GCP 每日資料
        try:
            gcp_series = self.gcp.get_daily_trend(days=days)
            for row in gcp_series:
                key = row.billing_date.isoformat()
                result.setdefault(key, {
                    "ai_anthropic": 0.0,
                    "ai_gemini": 0.0,
                    "ai_voyage": 0.0,
                    "gcp_total": 0.0,
                })
                result[key]["gcp_total"] = float(round(row.cost_usd, 2))
        except (GcpBillingUnavailable, NotImplementedError):
            pass

        # 若當月還沒有任何 ledger 資料，補足 days 天的零值
        if not result:
            for i in range(days):
                key = (now.date() - timedelta(days=i)).isoformat()
                result[key] = {
                    "ai_anthropic": 0.0,
                    "ai_gemini": 0.0,
                    "ai_voyage": 0.0,
                    "gcp_total": 0.0,
                }

        series = [{"date": k, **v} for k, v in sorted(result.items())]
        return self.ok({"days": days, "series": series})
