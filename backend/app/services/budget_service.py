"""BudgetService — Feature 33 Budget CRUD + GCP Sync orchestration.

負責：
- 單一 scope 預算修改（寫本地 + 觸發 GCP sync + 寫稽核）
- 整體調整（±N% 或設固定金額，依比例分配 + 同步）
- 手動解除停用（BUDGET_OVERRIDE）
- 告警評估（write BudgetAlertLog）
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import uuid

from sqlalchemy.orm import Session

from app.core.permissions import AuditAction
from app.models.audit_log import AdminAuditLog
from app.models.user import User
from app.repositories.ai_usage_repository import AiUsageRepository
from app.repositories.budget_alert_log_repository import BudgetAlertLogRepository
from app.repositories.budget_config_repository import BudgetConfigRepository
from app.services.base import BaseService
from app.services.gcp_budget_sync_service import GcpBudgetSyncService

_GLOBAL_SCALE_MIN = Decimal("0.50")
_GLOBAL_SCALE_MAX = Decimal("3.00")


class BudgetService(BaseService):
    def __init__(self, db: Session, gcp_sync: GcpBudgetSyncService | None = None):
        super().__init__(db)
        self.config_repo = BudgetConfigRepository(db)
        self.alert_repo = BudgetAlertLogRepository(db)
        self.ledger_repo = AiUsageRepository(db)
        self.gcp_sync = gcp_sync or GcpBudgetSyncService()

    # ------------------------------------------------------------------
    # 單一 scope 預算修改
    # ------------------------------------------------------------------

    def update_budget(
        self,
        *,
        super_admin: User,
        scope: str,
        new_limit_usd: Decimal,
        reason: str,
    ) -> dict:
        config = self.config_repo.get_by_scope(scope)
        if config is None:
            return self.error(f"budget_config not found for scope={scope}", 404)

        before_limit = float(Decimal(config.monthly_limit_usd))

        # 1. 寫本地
        self.config_repo.update_limit(scope, new_limit_usd, updated_by=super_admin.id)

        # 2. 同步至 GCP
        sync_result = self.gcp_sync.upsert_budget(
            scope=scope,
            monthly_limit_usd=new_limit_usd,
            warning_pct=config.warning_percent,
            degrade_pct=config.degrade_percent,
            disable_pct=config.disable_percent,
            existing_resource_name=config.gcp_budget_resource_name,
            gcp_sync_enabled=config.gcp_sync_enabled,
        )

        if sync_result.status in ("created", "updated"):
            self.config_repo.update_gcp_sync(
                scope=scope,
                gcp_budget_resource_name=sync_result.gcp_budget_resource_name,
                synced_at=datetime.now(timezone.utc),
            )

        # 3. 稽核
        audit_details = {
            "scope": scope,
            "before": before_limit,
            "after": float(new_limit_usd),
            "reason": reason,
            "gcp_sync": sync_result.status,
        }
        self._write_audit(
            super_admin.id, AuditAction.BUDGET_UPDATED,
            target_type="budget_config", target_id=config.id,
            details=audit_details,
        )

        self.db.commit()

        payload = {
            "scope": scope,
            "monthly_limit_usd": float(new_limit_usd),
            "gcp_sync_status": sync_result.status,
        }
        if sync_result.status == "failed":
            payload["warning"] = "GCP Native Budget 同步失敗，本地預算已更新"
        return self.ok(payload)

    # ------------------------------------------------------------------
    # 整體調整（±N% 或設固定金額，等比分配）
    # ------------------------------------------------------------------

    def global_scale(
        self,
        *,
        super_admin: User,
        scale_factor: Decimal | None = None,
        target_total_usd: Decimal | None = None,
        reason: str,
    ) -> dict:
        if scale_factor is None and target_total_usd is None:
            return self.error("必須提供 scale_factor 或 target_total_usd", 400)

        configs = self.config_repo.list_all()
        before_snapshot = {
            c.scope: float(Decimal(c.monthly_limit_usd)) for c in configs
        }
        total_before = sum(Decimal(str(v)) for v in before_snapshot.values())

        if scale_factor is not None:
            if not (_GLOBAL_SCALE_MIN <= scale_factor <= _GLOBAL_SCALE_MAX):
                return {
                    "error": True,
                    "status_code": 400,
                    "code": "BUDGET_SCALE_OUT_OF_RANGE",
                    "message": "整體調整範圍須介於 -50% 至 +200% 之間",
                }
            action = AuditAction.BUDGET_GLOBAL_SCALED
            new_totals = {
                c.scope: Decimal(c.monthly_limit_usd) * scale_factor
                for c in configs
            }
        else:
            assert target_total_usd is not None
            if total_before == 0:
                return self.error("current total is 0, cannot scale to target", 400)
            implied_factor = target_total_usd / total_before
            if not (_GLOBAL_SCALE_MIN <= implied_factor <= _GLOBAL_SCALE_MAX):
                return {
                    "error": True,
                    "status_code": 400,
                    "code": "BUDGET_SCALE_OUT_OF_RANGE",
                    "message": "目標金額等比換算超出 -50% ~ +200% 範圍",
                }
            action = AuditAction.BUDGET_GLOBAL_SET
            new_totals = {
                c.scope: Decimal(c.monthly_limit_usd) * implied_factor
                for c in configs
            }

        # 四捨五入到整數 USD
        rounded = {
            scope: value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            for scope, value in new_totals.items()
        }

        # 寫本地 + 同步 GCP
        sync_summary: dict[str, str] = {}
        for c in configs:
            new_limit = rounded[c.scope]
            self.config_repo.update_limit(c.scope, new_limit, updated_by=super_admin.id)

            result = self.gcp_sync.upsert_budget(
                scope=c.scope,
                monthly_limit_usd=new_limit,
                warning_pct=c.warning_percent,
                degrade_pct=c.degrade_percent,
                disable_pct=c.disable_percent,
                existing_resource_name=c.gcp_budget_resource_name,
                gcp_sync_enabled=c.gcp_sync_enabled,
            )
            if result.status in ("created", "updated"):
                self.config_repo.update_gcp_sync(
                    scope=c.scope,
                    gcp_budget_resource_name=result.gcp_budget_resource_name,
                    synced_at=datetime.now(timezone.utc),
                )
            sync_summary[c.scope] = result.status

        after_snapshot = {k: float(v) for k, v in rounded.items()}
        audit_details = {
            "scale_factor": float(scale_factor) if scale_factor else None,
            "target_total_usd": float(target_total_usd) if target_total_usd else None,
            "before": before_snapshot,
            "after": after_snapshot,
            "reason": reason,
            "gcp_sync": sync_summary,
        }
        self._write_audit(super_admin.id, action, target_type="budget_config", target_id=None, details=audit_details)

        self.db.commit()
        return self.ok({
            "before": before_snapshot,
            "after": after_snapshot,
            "gcp_sync": sync_summary,
        })

    # ------------------------------------------------------------------
    # 手動解除停用
    # ------------------------------------------------------------------

    def override_disable(
        self, *, super_admin: User, scope: str, reason: str
    ) -> dict:
        config = self.config_repo.get_by_scope(scope)
        if config is None:
            return self.error(f"budget_config not found for scope={scope}", 404)

        self.config_repo.update_state(scope, "active")

        self._write_audit(
            super_admin.id, AuditAction.BUDGET_OVERRIDE,
            target_type="budget_config", target_id=config.id,
            details={
                "scope": scope,
                "prev_state": config.current_state,
                "new_state": "active",
                "reason": reason,
            },
        )
        self.db.commit()
        return self.ok({"scope": scope, "state": "active"})

    # ------------------------------------------------------------------
    # 告警評估（由排程 / middleware 呼叫）
    # ------------------------------------------------------------------

    def evaluate_alerts(self) -> dict:
        """Iterate all scopes, compare current usage vs thresholds, emit alerts."""
        from app.services.gcp_billing_service import (
            GcpBillingService,
            GcpBillingUnavailable,
        )

        now = datetime.now(timezone.utc)
        fired: list[dict] = []
        gcp_billing = GcpBillingService()
        for c in self.config_repo.list_all():
            if c.scope == "GCP_TOTAL":
                try:
                    summary = gcp_billing.get_monthly_summary(now.year, now.month)
                    current = summary.total_usd
                except (GcpBillingUnavailable, NotImplementedError):
                    current = Decimal("0")
            else:
                provider = c.scope.removeprefix("AI_").lower()
                current, _, _ = self.ledger_repo.sum_month(provider, now.year, now.month)
            limit = Decimal(c.monthly_limit_usd)
            if limit <= 0:
                continue
            percent = (current / limit * Decimal("100"))

            new_state = c.current_state
            alert_type: str | None = None
            # GCP_TOTAL 不可被應用層 degrade/disable，所有超標一律 WARNING
            if c.scope == "GCP_TOTAL":
                if percent >= Decimal(c.warning_percent):
                    new_state = "warning"
                    alert_type = "WARNING"
                else:
                    new_state = "active"
            else:
                if percent >= Decimal(c.disable_percent):
                    new_state = "disabled"
                    alert_type = "DISABLED"
                elif percent >= Decimal(c.degrade_percent):
                    new_state = "degraded"
                    alert_type = "DEGRADE"
                elif percent >= Decimal(c.warning_percent):
                    new_state = "warning"
                    alert_type = "WARNING"
                else:
                    new_state = "active"

            if new_state != c.current_state:
                self.config_repo.update_state(c.scope, new_state)

            if alert_type:
                entry = self.alert_repo.create(
                    scope=c.scope,
                    alert_type=alert_type,
                    triggered_at_usd=current,
                    limit_usd=limit,
                    percent=percent.quantize(Decimal("0.01")),
                    notified_channels=["email", "in_app"],
                )
                fired.append({
                    "scope": c.scope,
                    "alert_type": alert_type,
                    "percent": float(round(percent, 2)),
                    "alert_id": str(entry.id),
                })

        self.db.commit()
        return self.ok({"fired": fired, "as_of": now.isoformat()})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_audit(
        self,
        admin_id: uuid.UUID,
        action: str,
        *,
        target_type: str,
        target_id: uuid.UUID | None,
        details: dict,
    ) -> None:
        log = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
        self.db.add(log)
