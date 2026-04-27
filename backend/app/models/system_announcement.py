"""SystemAnnouncement ORM Model — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class SystemAnnouncement(Base):
    """系統公告（顯示於 banner / dialog 等）。

    對應 DBML 表：system_announcements

    Attributes:
        title / content: 公告標題與內文
        type: info / warning / critical
        display_mode: banner / dialog / toast
        status: active / inactive / archived
        starts_at / ends_at: 生效起訖時間
        created_by: 發布管理員 user_id
    """

    __tablename__ = "system_announcements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="info")
    display_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="banner")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
