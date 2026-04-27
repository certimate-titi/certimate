"""Transaction ORM Model — ECPay payment transaction records."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class Transaction(Base):
    """金流交易紀錄（綠界 ECPay）。

    對應 DBML 表：transactions

    Attributes:
        user_id: 付款人（CASCADE）
        merchant_trade_no: 商家交易編號（unique，送綠界 key）
        target_plan: 升級目標方案（PRO / PRO_PLUS / ULTRA）
        amount: 交易金額
        status: pending / paid / failed / refunded
        payment_provider: 金流服務商（預設 ecpay）
        trade_no: 綠界回傳交易編號
        payment_type: 信用卡 / ATM / 超商等
        rtn_code: 綠界回傳碼
    """

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    merchant_trade_no: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )
    target_plan: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    payment_provider: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ecpay"
    )
    trade_no: Mapped[str | None] = mapped_column(String(50))
    payment_type: Mapped[str | None] = mapped_column(String(50))
    rtn_code: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
