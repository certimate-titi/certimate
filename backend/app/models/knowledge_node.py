"""KnowledgeNode ORM Model — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class KnowledgeNode(Base):
    """知識樹節點（資源解析後的學習鷹架）。

    對應 DBML 表：knowledge_nodes
    自關聯（parent_id）形成樹狀結構；同時掛在 Subject 與 Resource 上。

    Attributes:
        resource_id: 來源資源（CASCADE 刪除）
        subject_id: 所屬科目（科目隔離規則：禁止跨科目混入）
        parent_id: 父節點（NULL 為 root）
        name: 節點名稱
        depth: 樹深度
        sort_order: 同層排序
        source_page_number / source_timestamp_seconds / source_text:
            節點對應原資料來源錨點
        available_questions: 可命中此節點的題數快取
        exam_frequency: 考頻（高/中/低）
        support_strength: 使用者資料對節點的支撐強度（0.0-1.0）
        syllabus_topic_id: 對應考綱 topic
        node_source: syllabus / user_data / hybrid
        source_resource_count: 引用計數（cascade 刪除歸零即移除節點）
        tenant_id: 多租戶隔離鍵
    """

    __tablename__ = "knowledge_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE")
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id")
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id")
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    source_page_number: Mapped[int | None] = mapped_column(Integer)
    source_timestamp_seconds: Mapped[int | None] = mapped_column(Integer)
    source_text: Mapped[str | None] = mapped_column(Text)
    available_questions: Mapped[int] = mapped_column(Integer, default=0)
    exam_frequency: Mapped[str | None] = mapped_column(String(10))
    source_origin: Mapped[str] = mapped_column(String(20), server_default="document")
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="多租戶隔離鍵（NULL = 歸屬 public_b2c）",
        index=True,
    )
    # ── Mindmap architecture upgrade §3 — 骨架失焦處理 ───────────────
    support_strength: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.0", default=0.0,
        comment="使用者資料對此節點的支撐強度（0.0-1.0），< 0.3 顯示灰色「待補充」",
    )
    syllabus_topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="SET NULL"),
        nullable=True,
        comment="對應的考綱 topic id（骨架優先策略的錨點）",
    )
    node_source: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="user_data",
        comment="節點來源：syllabus / user_data / hybrid",
    )
    source_resource_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1",
        comment="引用計數：此節點被幾份資源引用；cascade 刪除時扣 1、歸零即刪 (PRD-034)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
