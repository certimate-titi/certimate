"""ScaffoldNodeLink ORM Model — Sprint 10 T80.

scaffold_node_links N:M 表：節點 ↔ 學習鷹架的多對多關聯。

由 parse pipeline 算 cosine similarity 後寫入（embedding 對應）；
unified extraction 重萃取時 relink；merge 時繼承。

對應 docs/ops/node-scaffold-pipeline-redesign-2026-05-09.md。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ScaffoldNodeLink(Base):
    """資源鷹架 ↔ 知識節點關聯。"""

    __tablename__ = "scaffold_node_links"
    __table_args__ = (
        UniqueConstraint("scaffold_id", "node_id", name="uq_snl_scaffold_node"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scaffold_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resource_scaffolds.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    # embedding / chapter_match / manual
    link_method: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
