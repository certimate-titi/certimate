"""AiModelRouting ORM Model — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class AiModelRouting(Base):
    """訂閱方案 × 任務類型對應的 AI 模型路由設定。

    對應 DBML 表：ai_model_routings
    供 ai_dispatcher 依 (plan, task_type) 查得 primary/fallback 模型。

    Attributes:
        plan: 訂閱方案（FREE / PRO / PRO_PLUS / ULTRA）
        task_type: 任務類型（chat / explain / generate_question 等）
        primary_model: 首選模型 ID
        fallback_model: 故障時備援模型 ID
    """

    __tablename__ = "ai_model_routings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan: Mapped[str] = mapped_column(String(50), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    primary_model: Mapped[str] = mapped_column(String(100), nullable=False)
    fallback_model: Mapped[str | None] = mapped_column(String(100))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
