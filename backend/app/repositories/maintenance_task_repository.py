"""MaintenanceTask Repository — SQLAlchemy implementation."""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.maintenance_task import MaintenanceTask


class MaintenanceTaskRepository:
    """維修任務資料存取 Repository。

    封裝 MaintenanceTask ORM 的儲存與查詢。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, task: MaintenanceTask) -> MaintenanceTask:
        """新增或更新維修任務並 commit。

        Args:
            task: 待儲存的 MaintenanceTask 實例。

        Returns:
            已 refresh 的 MaintenanceTask 實例。
        """
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def find_by_task_id(self, task_id: str) -> Optional[MaintenanceTask]:
        """依 task_id 查詢維修任務。

        Args:
            task_id: 任務唯一識別字串。

        Returns:
            MaintenanceTask 物件；若不存在回傳 None。
        """
        return self.session.query(MaintenanceTask).filter_by(task_id=task_id).first()

    def find_latest(self) -> Optional[MaintenanceTask]:
        """查詢最新建立的維修任務。

        Returns:
            ``created_at`` 最新的 MaintenanceTask；若無資料則回傳 None。
        """
        return self.session.query(MaintenanceTask).order_by(MaintenanceTask.created_at.desc()).first()
