"""FeatureFlag ORM Model — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class FeatureFlag(Base):
    """功能旗標（灰度/分階段釋出）。

    對應 DBML 表：feature_flags

    Attributes:
        flag_key: 旗標鍵（unique）
        enabled: 全域開關
        rollout_percentage: 隨機釋出百分比（0-100）
        target_plans: 鎖定特定方案（逗號分隔，例如 PRO,ULTRA）
    """

    __tablename__ = "feature_flags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    flag_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rollout_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_plans: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
