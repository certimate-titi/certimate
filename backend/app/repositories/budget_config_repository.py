"""BudgetConfig Repository — Feature 33 成本監控中心."""

from __future__ import annotations

from decimal import Decimal
import uuid

from sqlalchemy.orm import Session

from app.models.budget_config import BudgetConfig


class BudgetConfigRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_scope(self, scope: str) -> BudgetConfig | None:
        return (
            self.db.query(BudgetConfig)
            .filter(BudgetConfig.scope == scope)
            .first()
        )

    def list_all(self) -> list[BudgetConfig]:
        return self.db.query(BudgetConfig).order_by(BudgetConfig.scope).all()

    def update_limit(
        self,
        scope: str,
        new_limit: Decimal,
        updated_by: uuid.UUID,
    ) -> BudgetConfig:
        config = self.get_by_scope(scope)
        if config is None:
            raise ValueError(f"budget_config not found for scope={scope}")
        config.monthly_limit_usd = new_limit
        config.updated_by = updated_by
        self.db.flush()
        return config

    def update_thresholds(
        self,
        scope: str,
        warning_percent: int,
        degrade_percent: int,
        disable_percent: int,
        updated_by: uuid.UUID,
    ) -> BudgetConfig:
        config = self.get_by_scope(scope)
        if config is None:
            raise ValueError(f"budget_config not found for scope={scope}")
        config.warning_percent = warning_percent
        config.degrade_percent = degrade_percent
        config.disable_percent = disable_percent
        config.updated_by = updated_by
        self.db.flush()
        return config

    def update_state(
        self, scope: str, new_state: str
    ) -> BudgetConfig:
        config = self.get_by_scope(scope)
        if config is None:
            raise ValueError(f"budget_config not found for scope={scope}")
        config.current_state = new_state
        self.db.flush()
        return config

    def update_gcp_sync(
        self,
        scope: str,
        gcp_budget_resource_name: str | None,
        synced_at,
    ) -> BudgetConfig:
        config = self.get_by_scope(scope)
        if config is None:
            raise ValueError(f"budget_config not found for scope={scope}")
        config.gcp_budget_resource_name = gcp_budget_resource_name
        config.gcp_last_synced_at = synced_at
        self.db.flush()
        return config
