"""100 drop knowledge_nodes.depth CHECK constraint.

CEO 決策：知識節點不再限定深度。解除 091 引入的 chk_depth_range CHECK (1..3)
讓 LLM 自由判斷文件結構層級。
"""

from alembic import op


revision = "100"
down_revision = "099"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE knowledge_nodes DROP CONSTRAINT IF EXISTS chk_depth_range"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE knowledge_nodes "
        "ADD CONSTRAINT chk_depth_range CHECK (depth BETWEEN 1 AND 3) NOT VALID"
    )
