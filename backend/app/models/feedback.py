"""Feedback ORM Models — derived from erm.dbml feedbacks/feedback_attachments tables."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class FeedbackType(str, enum.Enum):
    """使用者回饋類型列舉。"""

    BUG = "BUG"
    FEATURE_REQUEST = "FEATURE_REQUEST"
    CONTENT_ERROR = "CONTENT_ERROR"
    OTHER = "OTHER"


class FeedbackStatus(str, enum.Enum):
    """使用者回饋處理狀態列舉。"""

    PENDING = "PENDING"
    REVIEWING = "REVIEWING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Feedback(Base):
    """使用者意見回饋主檔。

    對應 DBML 表：feedbacks
    一對多 feedback_attachments（透過 feedback_id）。

    Attributes:
        feedback_id: 對外案件編號（unique）
        user_id: 回饋者
        type: BUG / FEATURE_REQUEST / CONTENT_ERROR / OTHER
        subject / content: 主旨與內文
        status: PENDING / REVIEWING / RESOLVED / CLOSED
        admin_reply: 管理員回覆
        close_reason: 結案理由
    """

    __tablename__ = "feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    feedback_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )
    admin_reply: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    close_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FeedbackAttachment(Base):
    """意見回饋附件（截圖等）。

    對應 DBML 表：feedback_attachments
    從屬於 Feedback（feedback_id CASCADE）。

    Attributes:
        feedback_id: 所屬回饋
        file_path: 儲存路徑（GCS 或本地）
        file_size: 位元組數
        mime_type: 檔案 MIME
    """

    __tablename__ = "feedback_attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    feedback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("feedbacks.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
