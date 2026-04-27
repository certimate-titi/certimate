"""Coupon ORM Model — discount coupons."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class Coupon(Base):
    """優惠券（折扣碼）。

    對應 DBML 表：coupons

    Attributes:
        code: 折扣碼（unique，使用者輸入比對）
        discount_type: 折扣類型（percentage / fixed_amount）
        discount_value: 折扣值（百分比或固定金額）
        applicable_plans: 適用方案（逗號分隔字串）
        max_uses: 全域可用次數上限
        max_uses_per_user: 單一使用者可用次數上限
        used_count: 已使用次數
        status: active / paused / expired
    """

    __tablename__ = "coupons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    applicable_plans: Mapped[str | None] = mapped_column(Text)
    max_uses: Mapped[int | None] = mapped_column(Integer)
    max_uses_per_user: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
