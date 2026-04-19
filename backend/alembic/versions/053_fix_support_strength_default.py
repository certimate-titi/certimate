"""fix support_strength default (1.0 → 0.0) for cold-start semantics

Revision ID: 053
Revises: 052
Create Date: 2026-04-15

Patches the Strategy E cold-start bug: default 1.0 让所有节点看起来
「资料充足」，完全失去 Strategy E 的意义。Change default to 0.0 which
means「尚未测量」, and MindmapStrengthService.recompute_for_subject
fills the real value.
"""

from alembic import op
import sqlalchemy as sa


revision = "053"
down_revision = "052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Change column default
    op.alter_column(
        "knowledge_nodes",
        "support_strength",
        server_default="0.0",
    )
    # 2. Reset any existing nodes that got the legacy default.
    # NOTE: real value is computed lazily via MindmapStrengthService on
    # next extract() or explicit recompute.
    op.execute(
        "UPDATE knowledge_nodes SET support_strength = 0.0 WHERE support_strength = 1.0"
    )


def downgrade() -> None:
    op.alter_column(
        "knowledge_nodes",
        "support_strength",
        server_default="1.0",
    )
