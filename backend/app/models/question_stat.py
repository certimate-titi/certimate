"""QuestionStat ORM Model — derived from erm.dbml question_stats table."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class QuestionStat(Base):
    """以「使用者 × 知識節點」為粒度的答題統計（SR 排程依據）。

    對應 DBML 表：question_stats
    Unique（user_id, node_id）。

    Attributes:
        user_id: 使用者（CASCADE）
        node_id: 知識節點（CASCADE）
        success_count / fail_count: 累計成功/失敗次數
        ease_factor: SM-2 ease factor（預設 2.5）
        next_review_date: 下次複習日期
    """

    __tablename__ = "question_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "node_id", name="uq_question_stats_user_node"),
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
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    ease_factor: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=2.5)
    next_review_date: Mapped[date | None] = mapped_column(Date)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
