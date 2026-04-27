"""PlanQuota ORM Model — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class PlanQuota(Base):
    """訂閱方案配額設定。

    對應 DBML 表：plan_quotas

    Attributes:
        plan: 訂閱方案（unique，FREE / PRO / PRO_PLUS / ULTRA）
        monthly_uploads: 每月上傳檔數上限
        monthly_exams: 每月模擬考次數上限
        daily_ai_chats: 每日 AI 對話次數上限
        monthly_vision_pages: 每月 vision 頁數上限
        max_file_size_mb: 單檔大小上限
        monthly_resource_parse_limit: EPIC-035 每月 LLM 解析份數（-1 = 無限）
        updated_by: 最後修改的管理員
    """

    __tablename__ = "plan_quotas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    monthly_uploads: Mapped[int | None] = mapped_column(Integer)
    monthly_exams: Mapped[int | None] = mapped_column(Integer)
    daily_ai_chats: Mapped[int | None] = mapped_column(Integer)
    monthly_vision_pages: Mapped[int | None] = mapped_column(Integer)
    max_file_size_mb: Mapped[int | None] = mapped_column(Integer)
    monthly_resource_parse_limit: Mapped[int | None] = mapped_column(
        Integer, comment="EPIC-035 每月 LLM 解析份數；-1 代表無限"
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
