"""MergeConflict ORM Model — 知識樹合併衝突記錄。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class MergeConflict(Base):
    """知識樹合併衝突待審紀錄。

    對應 DBML 表：merge_conflicts
    當新進節點與既有節點高相似度時暫存供管理員裁定。

    Attributes:
        subject_id: 所屬科目
        existing_node_id: 既有節點（被疑似重複者）
        incoming_node_name: 新進節點名稱
        similarity: 相似度分數（0-1）
        status: pending_review / resolved
        suggestion: 系統建議動作（merge / keep_both / replace）
        resolution: 實際處理動作
        resolved_by / resolved_at: 處理人與時間
    """

    __tablename__ = "merge_conflicts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    existing_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id")
    )
    incoming_node_name: Mapped[str] = mapped_column(String(300), nullable=False)
    similarity: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending_review"
    )
    suggestion: Mapped[str] = mapped_column(String(30), nullable=False)
    resolution: Mapped[str | None] = mapped_column(String(30))
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
