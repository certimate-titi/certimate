"""AnomalyRecord Repository — SQLAlchemy implementation."""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.anomaly_record import AnomalyRecord


class AnomalyRecordRepository:
    """AnomalyRecord Repository - 使用 SQLAlchemy。"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, record: AnomalyRecord) -> AnomalyRecord:
        """保存 AnomalyRecord 到資料庫。"""
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def find_by_error_id(self, error_id: str) -> Optional[AnomalyRecord]:
        """根據 error_id 查詢。"""
        return self.session.query(AnomalyRecord).filter_by(error_id=error_id).first()

    def find_all(self) -> List[AnomalyRecord]:
        """查詢所有異常紀錄。"""
        return self.session.query(AnomalyRecord).order_by(AnomalyRecord.last_seen_at.desc()).all()
