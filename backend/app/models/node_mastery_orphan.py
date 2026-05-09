"""NodeMasteryOrphan ORM Model — Sprint 11 T96.

unified extraction 重建節點時找不到對應的 mastery backup。
admin 可手動 mapping 或客服協助移轉。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class NodeMasteryOrphan(Base):
    """重新分析後找不到對應的 mastery 備份。"""

    __tablename__ = "node_mastery_orphans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    old_node_name: Mapped[str] = mapped_column(String(300), nullable=False)
    base_mastery: Mapped[float | None] = mapped_column(Float)
    ease_factor: Mapped[float | None] = mapped_column(Float)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(20))
    correct_count: Mapped[int | None] = mapped_column(Integer)
    total_count: Mapped[int | None] = mapped_column(Integer)
    mastery_rate: Mapped[float | None] = mapped_column(Float)
    # pending / mapped / discarded
    resolution: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    mapped_to_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
