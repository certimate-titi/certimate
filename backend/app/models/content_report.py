"""ContentReport ORM Model — derived from erm.dbml."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class ReportStatus(str, enum.Enum):
    """檢舉處理狀態列舉。"""

    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ContentReport(Base):
    """使用者檢舉內容紀錄。

    對應 DBML 表：content_reports

    Attributes:
        report_ref: 檢舉案件對外編號（unique）
        reporter_id: 檢舉者識別字串
        report_type: 檢舉類型（spam / abuse / wrong_answer 等）
        target_type: 被檢舉實體型別（resource / question / comment …）
        target_id: 被檢舉實體 id
        status: 處理狀態（pending / resolved / dismissed）
        resolution_action: 處理動作（remove / warn / none）
        resolution_note: 處理備註
        resolved_by: 處理人員識別
    """

    __tablename__ = "content_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    report_ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    reporter_id: Mapped[str] = mapped_column(String(100), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ReportStatus.PENDING, nullable=False
    )
    resolution_action: Mapped[str | None] = mapped_column(String(50))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    resolved_by: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
