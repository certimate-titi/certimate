"""MergeHistory ORM Model — 知識樹合併歷史記錄。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class MergeHistory(Base):
    __tablename__ = "merge_histories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    trigger_source: Mapped[str] = mapped_column(String(20), nullable=False)
    trigger_name: Mapped[str] = mapped_column(String(255), nullable=False)
    nodes_added: Mapped[int] = mapped_column(Integer, default=0)
    nodes_merged: Mapped[int] = mapped_column(Integer, default=0)
    conflicts_count: Mapped[int] = mapped_column(Integer, default=0)
    merged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
