"""ScaffoldInteractionLog ORM Model — Sprint 1 P0 (T02).

記錄使用者與鷹架的互動事件（viewed / revealed / recall_self_rated）。
P0 純收集資料，P3 接 SM-2 排程演算法。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ScaffoldInteractionLog(Base):
    """鷹架互動事件流。

    對應 DBML 表：scaffold_interaction_log（migration 082）。

    Attributes:
        user_id: 互動者
        scaffold_id: 對應的學習鷹架
        event: 事件類型（"viewed" / "revealed" / "recall_self_rated"）
        recall_quality: 自評回想感（"none" / "partial" / "full"）— 僅 recall_self_rated 事件填
        created_at: 事件時間（後續 SM-2 排程算遺忘曲線用）
    """

    __tablename__ = "scaffold_interaction_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    scaffold_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resource_scaffolds.id", ondelete="CASCADE"),
        nullable=False,
    )
    event: Mapped[str] = mapped_column(String(32), nullable=False)
    recall_quality: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
