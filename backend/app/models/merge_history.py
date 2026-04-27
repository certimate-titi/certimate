"""MergeHistory ORM Model — 知識樹合併歷史記錄。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class MergeHistory(Base):
    """知識樹合併執行歷史。

    對應 DBML 表：merge_histories
    每次合併操作摘要：來源、新增/合併/衝突節點數。

    Attributes:
        subject_id: 所屬科目
        trigger_source: 觸發來源（resource / manual / batch）
        trigger_name: 來源描述（檔名或操作名）
        nodes_added: 新增節點數
        nodes_merged: 合併節點數
        conflicts_count: 待審衝突數
        merged_at: 合併執行時間
    """

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
