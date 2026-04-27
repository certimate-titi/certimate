"""AiUsageLedger ORM Model — derived from erm.dbml ai_usage_ledger table.

Feature 33 — 成本監控中心
記錄每次 AI 呼叫的 token 級明細，供成本監控與 Voyage 配額鎖查詢。
"""

from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class AiUsageLedger(Base):
    """AI 呼叫 token 級用量明細帳。

    對應 DBML 表：ai_usage_ledger
    Feature 33 — 成本監控中心；供月成本彙總與 Voyage 配額鎖查詢。

    Attributes:
        provider: 服務商（anthropic / gemini / openai / voyage）
        endpoint: 呼叫端點識別字串
        request_id: 上游 request id（供查 log）
        input_tokens: 輸入 token 數
        output_tokens: 輸出 token 數
        cost_usd: 該次呼叫成本（美金）
        billing_source: app（應用層計費）/ gcp（雲端帳單來源）
        feature: 觸發功能標籤（mock_exam / chat 等）
    """

    __tablename__ = "ai_usage_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String(128))
    request_id: Mapped[str | None] = mapped_column(String(128))
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), nullable=False, default=Decimal("0")
    )
    billing_source: Mapped[str] = mapped_column(
        String(16), nullable=False, default="app"
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    feature: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
