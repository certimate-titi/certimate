"""UserUsage ORM Model — derived from erm.dbml user_usage table."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class UserUsage(Base):
    """使用者每月用量配額追蹤。

    對應 DBML 表：user_usage
    Unique（user_id, period）；對照 plan_quotas 判斷是否超額。

    Attributes:
        user_id: 使用者（CASCADE）
        period: YYYY-MM 月份
        daily_ai_chats_used: 當日 AI 對話次數（每日重置）
        monthly_uploads_used: 當月上傳檔數
        monthly_exams_used: 當月模擬考次數
        monthly_vision_pages_used: 當月 vision 頁數
        last_reset_at: 最後重置時間
    """

    __tablename__ = "user_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="YYYY-MM format for monthly tracking"
    )
    daily_ai_chats_used: Mapped[int] = mapped_column(Integer, default=0)
    monthly_uploads_used: Mapped[int] = mapped_column(Integer, default=0)
    monthly_exams_used: Mapped[int] = mapped_column(Integer, default=0)
    monthly_vision_pages_used: Mapped[int] = mapped_column(Integer, default=0)
    last_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "period", name="uq_user_usage_user_period"),
    )
