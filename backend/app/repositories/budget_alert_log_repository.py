"""BudgetAlertLog Repository — Feature 33 成本監控中心."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.budget_alert_log import BudgetAlertLog


class BudgetAlertLogRepository:
    """預算告警日誌資料存取 Repository（Feature 33 成本監控中心）。

    封裝 BudgetAlertLog ORM 的寫入、查詢、解除告警標記，供 Budget Alert
    監控 service 使用。
    """

    def __init__(self, db: Session):
        """初始化 Repository。

        Args:
            db: SQLAlchemy Session。
        """
        self.db = db

    def create(
        self,
        *,
        scope: str,
        alert_type: str,  # WARNING / DEGRADE / DISABLED
        triggered_at_usd: Decimal,
        limit_usd: Decimal,
        percent: Decimal,
        notified_channels: list[str] | None = None,
    ) -> BudgetAlertLog:
        """寫入一筆預算告警紀錄。

        Args:
            scope: 預算 scope 名稱（例如 ``gemini``、``global``）。
            alert_type: 告警等級（``WARNING`` / ``DEGRADE`` / ``DISABLED``）。
            triggered_at_usd: 觸發告警當下的累積成本（美元）。
            limit_usd: 此 scope 的月度上限（美元）。
            percent: 觸發比例（0-100）。
            notified_channels: 已通知的管道清單；可為 None。

        Returns:
            已 flush 的 BudgetAlertLog 實例。
        """
        entry = BudgetAlertLog(
            scope=scope,
            alert_type=alert_type,
            triggered_at_usd=triggered_at_usd,
            limit_usd=limit_usd,
            percent=percent,
            notified_channels=notified_channels,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def list_recent(self, scope: str | None = None, limit: int = 50) -> list[BudgetAlertLog]:
        """查詢最近的告警紀錄。

        Args:
            scope: 預算 scope；若為 None 則回傳所有 scope。
            limit: 回傳筆數上限，預設 50。

        Returns:
            list of BudgetAlertLog，依 ``created_at`` 降冪排序。
        """
        q = self.db.query(BudgetAlertLog)
        if scope:
            q = q.filter(BudgetAlertLog.scope == scope)
        return q.order_by(BudgetAlertLog.created_at.desc()).limit(limit).all()

    def mark_resolved(self, alert_id, resolved_at: datetime) -> None:
        """將指定告警標記為已解除。

        若 alert_id 對應紀錄不存在則無動作。

        Args:
            alert_id: BudgetAlertLog 的主鍵 UUID。
            resolved_at: 解除告警時間。
        """
        entry = self.db.query(BudgetAlertLog).filter(BudgetAlertLog.id == alert_id).first()
        if entry:
            entry.resolved_at = resolved_at
            self.db.flush()
