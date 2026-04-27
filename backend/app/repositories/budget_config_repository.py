"""BudgetConfig Repository — Feature 33 成本監控中心."""

from __future__ import annotations

from decimal import Decimal
import uuid

from sqlalchemy.orm import Session

from app.models.budget_config import BudgetConfig


class BudgetConfigRepository:
    """預算設定資料存取 Repository（Feature 33 成本監控中心）。

    封裝 BudgetConfig ORM 的查詢與更新，每個 scope（例如 ``gemini``、
    ``global``）對應一筆設定，含月度上限、告警門檻、目前狀態與 GCP
    Budget API 同步資訊。
    """

    def __init__(self, db: Session):
        """初始化 Repository。

        Args:
            db: SQLAlchemy Session。
        """
        self.db = db

    def get_by_scope(self, scope: str) -> BudgetConfig | None:
        """依 scope 名稱查詢預算設定。

        Args:
            scope: 預算 scope（例如 ``gemini``、``anthropic``、``global``）。

        Returns:
            BudgetConfig 物件；若不存在回傳 None。
        """
        return (
            self.db.query(BudgetConfig)
            .filter(BudgetConfig.scope == scope)
            .first()
        )

    def list_all(self) -> list[BudgetConfig]:
        """列出所有預算設定，依 scope 名稱字母升冪排序。

        Returns:
            list of BudgetConfig。
        """
        return self.db.query(BudgetConfig).order_by(BudgetConfig.scope).all()

    def update_limit(
        self,
        scope: str,
        new_limit: Decimal,
        updated_by: uuid.UUID,
    ) -> BudgetConfig:
        """更新指定 scope 的月度預算上限。

        Args:
            scope: 預算 scope。
            new_limit: 新的月度上限（美元）。
            updated_by: 執行更新的管理員 UUID。

        Returns:
            更新後的 BudgetConfig 實例。

        Raises:
            ValueError: 找不到對應 scope 的設定。
        """
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
        """更新指定 scope 的告警門檻百分比。

        Args:
            scope: 預算 scope。
            warning_percent: 警告等級觸發比例（0-100）。
            degrade_percent: 降級等級觸發比例（0-100）。
            disable_percent: 停用等級觸發比例（0-100）。
            updated_by: 執行更新的管理員 UUID。

        Returns:
            更新後的 BudgetConfig 實例。

        Raises:
            ValueError: 找不到對應 scope 的設定。
        """
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
        """更新指定 scope 的目前狀態。

        Args:
            scope: 預算 scope。
            new_state: 新狀態字串（例如 ``NORMAL``、``WARNING``、``DEGRADED``、``DISABLED``）。

        Returns:
            更新後的 BudgetConfig 實例。

        Raises:
            ValueError: 找不到對應 scope 的設定。
        """
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
        """更新與 GCP Budget API 同步的中繼資料。

        Args:
            scope: 預算 scope。
            gcp_budget_resource_name: GCP Budget 資源名稱；可為 None。
            synced_at: 最後同步時間（datetime）。

        Returns:
            更新後的 BudgetConfig 實例。

        Raises:
            ValueError: 找不到對應 scope 的設定。
        """
        config = self.get_by_scope(scope)
        if config is None:
            raise ValueError(f"budget_config not found for scope={scope}")
        config.gcp_budget_resource_name = gcp_budget_resource_name
        config.gcp_last_synced_at = synced_at
        self.db.flush()
        return config
