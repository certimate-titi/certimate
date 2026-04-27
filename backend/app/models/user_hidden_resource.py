"""UserHiddenResource ORM Model — per-user soft-hide for non-owned resources."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class UserHiddenResource(Base):
    """使用者軟隱藏「非自有資源」記錄（Per-user 隱藏狀態）。

    對應 DBML 表：user_hidden_resources
    複合主鍵（user_id, resource_id）；用於分享/平台資源的個人隱藏不影響他人。

    Attributes:
        user_id: 隱藏該資源的使用者（CASCADE）
        resource_id: 被隱藏的資源（CASCADE）
        hidden_at: 隱藏時間
    """

    __tablename__ = "user_hidden_resources"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True
    )
    hidden_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
