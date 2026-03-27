"""MaintenanceSchedule Repository — SQLAlchemy implementation."""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.maintenance_notification import MaintenanceNotification


class MaintenanceScheduleRepository:
    """MaintenanceSchedule Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, schedule: MaintenanceSchedule) -> MaintenanceSchedule:
        """保存 MaintenanceSchedule 到資料庫。"""
        self.session.add(schedule)
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def find_active(self) -> Optional[MaintenanceSchedule]:
        """查詢目前啟用的維修排程。"""
        return self.session.query(MaintenanceSchedule).filter_by(status="active").first()

    def find_latest(self) -> Optional[MaintenanceSchedule]:
        """查詢最新建立的排程。"""
        return self.session.query(MaintenanceSchedule).order_by(MaintenanceSchedule.created_at.desc()).first()

    def find_notifications_by_schedule(self, schedule_id) -> List[MaintenanceNotification]:
        """查詢排程的所有通知。"""
        return self.session.query(MaintenanceNotification).filter_by(schedule_id=schedule_id).all()

    def save_notification(self, notification: MaintenanceNotification) -> MaintenanceNotification:
        """保存 MaintenanceNotification。"""
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification
