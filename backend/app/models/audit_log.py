"""AdminAuditLog ORM Model — derived from erm.dbml admin_audit_logs table."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class AdminAuditLog(Base):
    """平台管理員操作稽核紀錄。

    對應 DBML 表：admin_audit_logs
    記錄管理員對任意 target 的操作以供事後追溯。

    Attributes:
        admin_id: 操作管理員 user_id
        action: 動作字串（例如 user.suspend）
        target_type: 目標實體型別（user / resource / refund …）
        target_id: 目標主鍵
        details: JSON 額外明細
        ip_address / user_agent: 來源資訊
    """

    __tablename__ = "admin_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    details: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
