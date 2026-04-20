"""Add daily_quest_progress for per-user per-day quest tracking.

Revision ID: 060
Revises: 059
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "060"
down_revision = "059"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_quest_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quest_date", sa.Date(), nullable=False),
        sa.Column("quest_key", sa.String(64), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "quest_date", "quest_key", name="uq_daily_quest_user_date_key"),
    )
    op.create_index("ix_daily_quest_user_date", "daily_quest_progress", ["user_id", "quest_date"])


def downgrade() -> None:
    op.drop_index("ix_daily_quest_user_date", table_name="daily_quest_progress")
    op.drop_table("daily_quest_progress")
