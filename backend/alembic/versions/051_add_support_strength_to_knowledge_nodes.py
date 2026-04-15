"""add support_strength + syllabus_topic_id to knowledge_nodes

Revision ID: 051
Revises: 050
Create Date: 2026-04-15

Mindmap architecture upgrade — §3 骨架失焦處理
- support_strength FLOAT (0.0-1.0): 使用者資料對該節點的支撐強度
- syllabus_topic_id UUID: 節點對應的考綱 topic（錨點穩定性來源）
- node_source VARCHAR: 來源類型（syllabus / user_data / hybrid）
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "051"
down_revision = "050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "knowledge_nodes",
        sa.Column(
            "support_strength",
            sa.Float,
            nullable=False,
            server_default="0.0",
            comment=(
                "使用者資料對此節點的支撐強度（0.0-1.0），< 0.3 顯示灰色「待補充」。"
                "預設 0.0 代表「尚未測量」，MindmapStrengthService.recompute_for_subject 會填入真實值。"
            ),
        ),
    )
    op.add_column(
        "knowledge_nodes",
        sa.Column(
            "syllabus_topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("syllabus_topics.id", ondelete="SET NULL"),
            nullable=True,
            comment="對應的考綱 topic id（骨架優先策略的錨點）",
        ),
    )
    op.add_column(
        "knowledge_nodes",
        sa.Column(
            "node_source",
            sa.String(16),
            nullable=False,
            server_default="user_data",
            comment="節點來源：syllabus（官方考綱）/ user_data（使用者資料）/ hybrid",
        ),
    )
    op.create_index(
        "idx_knowledge_nodes_syllabus_topic",
        "knowledge_nodes",
        ["syllabus_topic_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_knowledge_nodes_syllabus_topic",
        table_name="knowledge_nodes",
    )
    op.drop_column("knowledge_nodes", "node_source")
    op.drop_column("knowledge_nodes", "syllabus_topic_id")
    op.drop_column("knowledge_nodes", "support_strength")
