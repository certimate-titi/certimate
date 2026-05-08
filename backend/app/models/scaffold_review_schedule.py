"""ScaffoldReviewSchedule ORM Model — Sprint 5 P4 (T44).

對每個 (user_id, scaffold_id) 維護 SM-2 演算法狀態。
由 SM-2 演算法（services/sm2_service.py）依 scaffold_interaction_log
的 recall_self_rated 事件 + recall_quality 計算下次複習時間。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime, Float, ForeignKey, Integer, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ScaffoldReviewSchedule(Base):
    """SM-2 排程狀態表。

    對應 DBML 表：scaffold_review_schedule（migration 086）。

    Attributes:
        user_id: 使用者
        scaffold_id: 鷹架
        ease_factor: SM-2 記憶因子（初始 2.5，範圍 1.3-3.0+）
        interval_days: 下次複習間隔天數
        repetitions: 連續答對次數
        next_review_at: 下次該複習時間（給 /due endpoint 過濾用）
        last_reviewed_at: 上次自評時間
    """

    __tablename__ = "scaffold_review_schedule"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "scaffold_id", name="uq_scaffold_review_user_scaffold"
        ),
    )

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
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
