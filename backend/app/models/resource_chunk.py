"""ResourceChunk ORM Model — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
import uuid

from app.models import Base


class ResourceChunk(Base):
    """資源切片 + 1024 維 embedding（pgvector）。

    對應 DBML 表：resource_chunks
    從屬於 Resource（CASCADE）；可選對應 KnowledgeNode；RLS 啟用。

    Attributes:
        resource_id: 來源資源
        node_id: 對應知識節點（SET NULL）
        chunk_index: 切片序號
        content: 切片文字
        token_count: token 數
        source_page_start / source_page_end: 對應頁碼範圍
        anchor_id: 物理錨點（PDF page、HTML heading、YouTube timestamp）
        highlight_line_start/end / highlight_char_start/end: 原文高亮範圍
        embedding: 1024 維向量（pgvector）
        is_deleted: 軟刪除（從檢索與強度計算排除）
        tenant_id: 多租戶隔離鍵（RLS 強制）
    """

    __tablename__ = "resource_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id", ondelete="SET NULL")
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source_page_start: Mapped[int | None] = mapped_column(Integer)
    source_page_end: Mapped[int | None] = mapped_column(Integer)
    # 物理級跳轉：精確定位到文件中的段落
    anchor_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="文件內錨點 ID（PDF: page_N, HTML: heading ID, YouTube: timestamp）",
    )
    highlight_line_start: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="原文高亮起始行（1-based）",
    )
    highlight_line_end: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="原文高亮結束行（1-based, inclusive）",
    )
    highlight_char_start: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="原文高亮起始字元偏移（0-based）",
    )
    highlight_char_end: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="原文高亮結束字元偏移（0-based, exclusive）",
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    embedding = mapped_column(Vector(1024))
    tenant_id = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="多租戶隔離鍵（NULL = 歸屬 public_b2c）— RLS 強制啟用",
        index=True,
    )
    # T2-A 軟刪剪枝
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false",
        comment="軟刪標記 — true 時從檢索與強度計算排除",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
