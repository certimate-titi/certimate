"""Add streak tracking fields to users for dashboard LearningStreak.

Revision ID: 057
Revises: 056
"""

from alembic import op
import sqlalchemy as sa


revision = "057"
down_revision = "056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("freezes_remaining", sa.Integer(), nullable=False, server_default="2"))
    op.add_column("users", sa.Column("freezes_per_week", sa.Integer(), nullable=False, server_default="2"))
    op.add_column("users", sa.Column("last_active_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("freeze_consumed_today", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("users", "freeze_consumed_today")
    op.drop_column("users", "last_active_date")
    op.drop_column("users", "freezes_per_week")
    op.drop_column("users", "freezes_remaining")
    op.drop_column("users", "longest_streak")
    op.drop_column("users", "current_streak")
