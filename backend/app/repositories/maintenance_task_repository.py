"""MaintenanceTask Repository — SQLAlchemy implementation."""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.maintenance_task import MaintenanceTask


class MaintenanceTaskRepository:
    """MaintenanceTask Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, task: MaintenanceTask) -> MaintenanceTask:
        """保存 MaintenanceTask 到資料庫。"""
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def find_by_task_id(self, task_id: str) -> Optional[MaintenanceTask]:
        """根據 task_id 查詢。"""
        return self.session.query(MaintenanceTask).filter_by(task_id=task_id).first()

    def find_latest(self) -> Optional[MaintenanceTask]:
        """查詢最新建立的任務。"""
        return self.session.query(MaintenanceTask).order_by(MaintenanceTask.created_at.desc()).first()
