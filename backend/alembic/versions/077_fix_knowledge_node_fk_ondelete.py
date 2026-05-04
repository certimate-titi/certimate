"""Fix FK ondelete on knowledge_nodes references — Bug fix L-resource-delete.

問題：刪除 resource 時 cascade 到 knowledge_nodes，但 questions.node_id 與
knowledge_nodes.parent_id FK 預設 NO ACTION 阻擋刪除 → IntegrityError 500。

修法：
- questions.node_id → SET NULL（題目保留，僅斷開節點關聯）
- questions.suggested_node_id → SET NULL（同上）
- knowledge_nodes.parent_id → CASCADE（父節點刪除時，子節點亦刪除）

Revision ID: 077
Revises: 076
"""

from alembic import op


revision = "077"
down_revision = "076"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # questions.node_id: NO ACTION → SET NULL
    op.execute("ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_node_id_fkey")
    op.create_foreign_key(
        "questions_node_id_fkey",
        "questions", "knowledge_nodes",
        ["node_id"], ["id"],
        ondelete="SET NULL",
    )

    # questions.suggested_node_id: NO ACTION → SET NULL
    op.execute("ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_suggested_node_id_fkey")
    op.create_foreign_key(
        "questions_suggested_node_id_fkey",
        "questions", "knowledge_nodes",
        ["suggested_node_id"], ["id"],
        ondelete="SET NULL",
    )

    # knowledge_nodes.parent_id: NO ACTION → CASCADE
    op.execute("ALTER TABLE knowledge_nodes DROP CONSTRAINT IF EXISTS knowledge_nodes_parent_id_fkey")
    op.create_foreign_key(
        "knowledge_nodes_parent_id_fkey",
        "knowledge_nodes", "knowledge_nodes",
        ["parent_id"], ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # 還原為 NO ACTION（不建議，會重現 IntegrityError）
    op.execute("ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_node_id_fkey")
    op.create_foreign_key(
        "questions_node_id_fkey",
        "questions", "knowledge_nodes",
        ["node_id"], ["id"],
    )
    op.execute("ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_suggested_node_id_fkey")
    op.create_foreign_key(
        "questions_suggested_node_id_fkey",
        "questions", "knowledge_nodes",
        ["suggested_node_id"], ["id"],
    )
    op.execute("ALTER TABLE knowledge_nodes DROP CONSTRAINT IF EXISTS knowledge_nodes_parent_id_fkey")
    op.create_foreign_key(
        "knowledge_nodes_parent_id_fkey",
        "knowledge_nodes", "knowledge_nodes",
        ["parent_id"], ["id"],
    )
