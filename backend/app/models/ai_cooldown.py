"""AiCooldown ORM Model — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class AiCooldown(Base):
    """AI 功能冷卻紀錄（避免使用者短時間重複觸發高成本任務）。

    對應 DBML 表：ai_cooldowns

    Attributes:
        user_id: 受冷卻限制的使用者
        reason: 冷卻原因（例如 mock_exam_generation）
        cooldown_until: 冷卻解除時間戳記
    """

    __tablename__ = "ai_cooldowns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(100))
    cooldown_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
