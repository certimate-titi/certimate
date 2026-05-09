"""092 node_mastery_orphans — Sprint 11 T96.

unified extraction 重建節點時，找不到對應的 mastery backup 寫入此表，
admin 可手動 mapping 或客服協助。

對應 docs/ops/extraction-lifecycle-redesign-2026-05-09.md L1 止血方案。
"""

from alembic import op
import sqlalchemy as sa


revision = "092"
down_revision = "091"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_mastery_orphans",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("subject_id", sa.UUID(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_node_name", sa.String(300), nullable=False),
        sa.Column("base_mastery", sa.Float()),
        sa.Column("ease_factor", sa.Float()),
        sa.Column("last_tested_at", sa.DateTime(timezone=True)),
        sa.Column("next_review_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20)),
        sa.Column("correct_count", sa.Integer()),
        sa.Column("total_count", sa.Integer()),
        sa.Column("mastery_rate", sa.Float()),
        # 解決方案
        sa.Column("resolution", sa.String(20), nullable=False, server_default="pending"),
        # pending / mapped / discarded
        sa.Column("mapped_to_node_id", sa.UUID(), sa.ForeignKey("knowledge_nodes.id", ondelete="SET NULL")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_nmo_subject_pending",
                    "node_mastery_orphans", ["subject_id", "resolution"])


def downgrade() -> None:
    op.drop_index("ix_nmo_subject_pending", table_name="node_mastery_orphans")
    op.drop_table("node_mastery_orphans")
