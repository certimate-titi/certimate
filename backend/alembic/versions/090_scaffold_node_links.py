"""090 scaffold_node_links N:M + knowledge_nodes.embedding — Sprint 10 T80.

教育顧問×CTO 聯合會議結論（docs/ops/node-scaffold-pipeline-redesign-2026-05-09.md）：
解決「節點 ↔ 鷹架對不起來」架構斷層 — 加 N:M 表 + 節點 embedding 欄位
讓 parse pipeline 算 cosine similarity 預先寫入關聯。
"""

from alembic import op
import sqlalchemy as sa


revision = "090"
down_revision = "089"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # KnowledgeNode 加 embedding 欄位（與 resource_scaffolds.embedding 對應）
    op.execute(
        "ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS embedding vector(1024)"
    )

    # N:M 關聯表
    op.create_table(
        "scaffold_node_links",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("scaffold_id", sa.UUID(), sa.ForeignKey("resource_scaffolds.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_id", sa.UUID(), sa.ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("link_method", sa.String(20), nullable=False),  # embedding / chapter_match / manual
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("scaffold_id", "node_id", name="uq_snl_scaffold_node"),
    )
    op.create_index("ix_snl_node_sim", "scaffold_node_links", ["node_id", sa.text("similarity DESC")])
    op.create_index("ix_snl_scaffold", "scaffold_node_links", ["scaffold_id"])


def downgrade() -> None:
    op.drop_index("ix_snl_scaffold", table_name="scaffold_node_links")
    op.drop_index("ix_snl_node_sim", table_name="scaffold_node_links")
    op.drop_table("scaffold_node_links")
    # 不刪 knowledge_nodes.embedding（其他用途可能用到）
