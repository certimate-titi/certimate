"""Fix merge_conflicts.existing_node_id FK ondelete (補漏 077).

Revision ID: 078
Revises: 077
"""

from alembic import op


revision = "078"
down_revision = "077"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE merge_conflicts DROP CONSTRAINT IF EXISTS merge_conflicts_existing_node_id_fkey")
    op.create_foreign_key(
        "merge_conflicts_existing_node_id_fkey",
        "merge_conflicts", "knowledge_nodes",
        ["existing_node_id"], ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.execute("ALTER TABLE merge_conflicts DROP CONSTRAINT IF EXISTS merge_conflicts_existing_node_id_fkey")
    op.create_foreign_key(
        "merge_conflicts_existing_node_id_fkey",
        "merge_conflicts", "knowledge_nodes",
        ["existing_node_id"], ["id"],
    )
