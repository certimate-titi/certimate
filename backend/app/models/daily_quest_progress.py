"""DailyQuestProgress ORM — tracks per-user, per-day quest progress."""

import uuid
from datetime import date as date_type, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class DailyQuestProgress(Base):
    """使用者每日任務進度。

    對應 DBML 表：daily_quest_progress
    Unique（user_id, quest_date, quest_key）。

    Attributes:
        user_id: 使用者
        quest_date: 任務所屬日期
        quest_key: 任務鍵（例如 daily_practice_10）
        progress: 目前進度數值
        target: 完成所需目標數
        completed_at: 完成時間（NULL 代表尚未完成）
        meta: JSONB 額外資訊
    """

    __tablename__ = "daily_quest_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "quest_date", "quest_key", name="uq_daily_quest_user_date_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quest_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    quest_key: Mapped[str] = mapped_column(String(64), nullable=False)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
