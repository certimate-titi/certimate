"""歷史考試目錄 — 存放爬蟲匯入的考試元資料（考試代碼/類科/科目）。"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class HistoricalExam(Base):
    __tablename__ = "historical_exams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exam_code: Mapped[str] = mapped_column(String(50), nullable=False, comment="考試代碼，如 114010 或 FIN114")
    category_code: Mapped[str | None] = mapped_column(String(100), comment="類科代碼，如 501 或 securities")
    subject_code: Mapped[str | None] = mapped_column(String(100), comment="科目代碼，如 0101 或 derivatives_session01")
    exam_name: Mapped[str | None] = mapped_column(String(255), comment="考試名稱，如 114年初等考試")
    category_name: Mapped[str | None] = mapped_column(String(255), comment="類科名稱，如 一般行政")
    subject_name: Mapped[str | None] = mapped_column(String(255), comment="科目名稱，如 國文")
    source: Mapped[str | None] = mapped_column(
        String(255), server_default="考選部考畢試題查詢平臺", comment="資料來源"
    )
    total_questions: Mapped[int | None] = mapped_column(Integer, comment="題目總數")
    year: Mapped[int | None] = mapped_column(Integer, comment="民國年")
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True, comment="多租戶隔離鍵"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "exam_code", "category_code", "subject_code",
            name="uq_historical_exam_identity",
        ),
    )
