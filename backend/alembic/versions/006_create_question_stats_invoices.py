"""create question_stats table

Revision ID: 006
Revises: 005
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "question_stats",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("success_count", sa.Integer, server_default="0"),
        sa.Column("fail_count", sa.Integer, server_default="0"),
        sa.Column("ease_factor", sa.Numeric(4, 2), server_default="2.5"),
        sa.Column("next_review_date", sa.Date),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "node_id", name="uq_question_stats_user_node"),
    )


def downgrade() -> None:
    op.drop_table("question_stats")
