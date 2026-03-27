"""Create user_usage table.

Revision ID: 013
Revises: 012
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_usage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("daily_ai_chats_used", sa.Integer, server_default="0"),
        sa.Column("monthly_uploads_used", sa.Integer, server_default="0"),
        sa.Column("monthly_exams_used", sa.Integer, server_default="0"),
        sa.Column("monthly_vision_pages_used", sa.Integer, server_default="0"),
        sa.Column("last_reset_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "period", name="uq_user_usage_user_period"),
    )
    op.create_index("idx_user_usage_user_id", "user_usage", ["user_id"])
    op.create_index("idx_user_usage_period", "user_usage", ["period"])


def downgrade() -> None:
    op.drop_index("idx_user_usage_period", "user_usage")
    op.drop_index("idx_user_usage_user_id", "user_usage")
    op.drop_table("user_usage")
