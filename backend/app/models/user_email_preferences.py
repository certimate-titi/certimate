"""UserEmailPreferences ORM Model — Sprint 9 議題 E.

每用戶一筆，記錄 4 個 retention email 的開關 + unsubscribe_token JWT。

事務型（parse_failure）強制 enabled = true（API 拒絕關閉，DB 直改也會被
EmailService 邏輯忽略）。
行銷型（daily_review / weekly_report / streak_warning）用戶可自行關閉。
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class UserEmailPreferences(Base):
    """每用戶 retention email 偏好。對應 docs/ops/retention-email-templates spec。"""

    __tablename__ = "user_email_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    # 行銷型 — 預設開，可關
    daily_review_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekly_report_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    streak_warning_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # 事務型 — DB 欄位存在但 EmailService 永遠視為 true（PDPA 例外：服務必要通知）
    parse_failure_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # JWT permanent token — 退訂連結用（HS256, sub=user_id, purpose=email_unsubscribe）
    unsubscribe_token: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EmailSendLog(Base):
    """每次 retention email 寄送結果（成功 / 失敗 / 略過）。

    用途：
    - 24h 重寄防護（同 user_id + trigger_id 不重寄）
    - A/B 測試指標彙總（subject_variant）
    - 客服查詢「為什麼用戶沒收到信」
    """

    __tablename__ = "email_send_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    trigger_id: Mapped[str] = mapped_column(String(50), nullable=False)
    # sent / skipped / failed
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # 跳過 / 失敗原因（FREE_NOT_ELIGIBLE / ALREADY_SENT_TODAY / SMTP_ERROR / ...）
    reason: Mapped[str | None] = mapped_column(String(255))
    # A/B 變體：A / B（subject 行差異）
    subject_variant: Mapped[str | None] = mapped_column(String(8))
    # 寄出的 subject 完整文字（事後分析用）
    subject: Mapped[str | None] = mapped_column(String(255))
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
