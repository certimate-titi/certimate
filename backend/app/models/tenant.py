"""Tenant ORM Model — derived from erm.dbml (Table: tenants)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, JSON, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class Tenant(Base):
    """多租戶隔離基礎 — B2B 機構 / B2C 散客統一入口。"""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
        comment="唯一識別碼，如 public_b2c / institution_xyz",
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="顯示名稱")
    plan_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="b2c",
        comment="b2c | b2b_basic | b2b_pro | b2b_enterprise",
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    max_users: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="B2B 授權人數上限，B2C 為 NULL"
    )
    storage_quota_bytes: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="儲存容量配額，NULL = 無限制"
    )
    llm_monthly_budget_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="每月 LLM 預算上限（美元），NULL = 無限制"
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="可擴充的租戶設定（白名單 domain, SSO config…）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """除錯用簡短表示。

        Returns:
            str: 包含 slug、plan_tier、is_active 的字串
        """
        return f"<Tenant(slug='{self.slug}', plan_tier='{self.plan_tier}', is_active={self.is_active})>"
