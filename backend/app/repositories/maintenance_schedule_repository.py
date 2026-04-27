"""MaintenanceSchedule Repository — SQLAlchemy implementation."""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.maintenance_notification import MaintenanceNotification


class MaintenanceScheduleRepository:
    """維修排程資料存取 Repository。

    封裝 MaintenanceSchedule 與 MaintenanceNotification ORM 的儲存
    與查詢，供系統維修通知 service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, schedule: MaintenanceSchedule) -> MaintenanceSchedule:
        """新增或更新維修排程並 commit。

        Args:
            schedule: 待儲存的 MaintenanceSchedule 實例。

        Returns:
            已 refresh 的 MaintenanceSchedule 實例。
        """
        self.session.add(schedule)
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def find_active(self) -> Optional[MaintenanceSchedule]:
        """查詢目前 ``status="active"`` 的維修排程。

        Returns:
            啟用中的 MaintenanceSchedule；若無則回傳 None。
        """
        return self.session.query(MaintenanceSchedule).filter_by(status="active").first()

    def find_latest(self) -> Optional[MaintenanceSchedule]:
        """查詢最新建立的排程。

        Returns:
            ``created_at`` 最新的 MaintenanceSchedule；若無資料則回傳 None。
        """
        return self.session.query(MaintenanceSchedule).order_by(MaintenanceSchedule.created_at.desc()).first()

    def find_notifications_by_schedule(self, schedule_id) -> List[MaintenanceNotification]:
        """查詢排程關聯的所有通知紀錄。

        Args:
            schedule_id: MaintenanceSchedule UUID。

        Returns:
            list of MaintenanceNotification。
        """
        return self.session.query(MaintenanceNotification).filter_by(schedule_id=schedule_id).all()

    def save_notification(self, notification: MaintenanceNotification) -> MaintenanceNotification:
        """新增或更新維修通知並 commit。

        Args:
            notification: 待儲存的 MaintenanceNotification 實例。

        Returns:
            已 refresh 的 MaintenanceNotification 實例。
        """
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification
