"""NodeMastery ORM Model — 個人知識節點掌握度（含記憶衰退參數）.

v2 新增：base_mastery, ease_factor, last_tested_at, next_review_at, status
支援 SM-2 狀態機 + read-time decay 計算。
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, Integer, Numeric, String, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class NodeMastery(Base):
    """個人知識節點掌握度（含 SM-2 + 衰退參數）。

    對應 DBML 表：node_mastery
    Unique（user_id, node_id）；驅動 spaced repetition 推薦複習。

    Attributes:
        user_id: 學習者（CASCADE）
        node_id: 對應知識節點（CASCADE）
        correct_count / total_count / mastery_rate: 累積答題統計（v1 相容）
        color: UI 顏色標籤
        base_mastery: 基礎掌握度 0.0-1.0（僅由正式考試更新）
        ease_factor: SM-2 ease factor（最小 1.3）
        last_tested_at: 最後一次正式測驗時間
        next_review_at: 建議下次複習時間
        status: UNSEEN / CRITICAL / PENDING / MASTERED
    """

    __tablename__ = "node_mastery"
    __table_args__ = (
        UniqueConstraint("user_id", "node_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False
    )

    # ── 舊欄位（保留向後相容）──────────────────────────────────
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    mastery_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    color: Mapped[str | None] = mapped_column(String(10))

    # ── v2 新增：SM-2 + Decay 參數 ─────────────────────────────
    base_mastery: Mapped[float] = mapped_column(
        Float, default=0.0,
        comment="基礎掌握度（0.0~1.0），僅由正式考試更新",
    )
    ease_factor: Mapped[float] = mapped_column(
        Float, default=2.5,
        comment="SM-2 ease factor（控制衰退速度，最小 1.3）",
    )
    last_tested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="最後一次正式考試時間",
    )
    next_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="下次建議複習時間（超過此時間開始衰退）",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="UNSEEN",
        comment="UNSEEN / CRITICAL / PENDING / MASTERED",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
