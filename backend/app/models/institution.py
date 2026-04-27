"""Institution ORM Model — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class Institution(Base):
    """B2B 教育機構主檔。

    對應 DBML 表：institutions
    每個 Institution 對應一位 admin user 與多個 student_groups。

    Attributes:
        name: 機構名稱
        admin_user_id: 機構管理員 user_id
        dpa_signed_at / dpa_signer_name: 資料處理協議簽署資訊
        edu_student_limit: 學生數上限（預設 30）
        surcharge_confirmed: 超量加價是否確認
    """

    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    dpa_signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dpa_signer_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    edu_student_limit: Mapped[int] = mapped_column(Integer, default=30)
    surcharge_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
