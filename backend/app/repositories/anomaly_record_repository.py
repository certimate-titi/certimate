"""AnomalyRecord Repository — SQLAlchemy implementation."""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.anomaly_record import AnomalyRecord


class AnomalyRecordRepository:
    """異常紀錄資料存取 Repository。

    封裝 AnomalyRecord ORM 的儲存與查詢，供維運監控 service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save(self, record: AnomalyRecord) -> AnomalyRecord:
        """新增或更新異常紀錄並 commit。

        Args:
            record: 待儲存的 AnomalyRecord 實例。

        Returns:
            已 refresh 的 AnomalyRecord 實例。
        """
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def find_by_error_id(self, error_id: str) -> Optional[AnomalyRecord]:
        """依 error_id 查詢異常紀錄。

        Args:
            error_id: 異常事件唯一識別字串。

        Returns:
            AnomalyRecord 物件；若不存在回傳 None。
        """
        return self.session.query(AnomalyRecord).filter_by(error_id=error_id).first()

    def find_all(self) -> List[AnomalyRecord]:
        """查詢所有異常紀錄，依最近發生時間降冪排序。

        Returns:
            list of AnomalyRecord，依 ``last_seen_at`` 降冪排序。
        """
        return self.session.query(AnomalyRecord).order_by(AnomalyRecord.last_seen_at.desc()).all()
