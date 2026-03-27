"""Create weekly_reports table.

Revision ID: 015
Revises: 014
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weekly_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_week", sa.Date, nullable=False),
        sa.Column("study_hours", sa.Numeric(5, 1)),
        sa.Column("exams_completed", sa.Integer),
        sa.Column("questions_answered", sa.Integer),
        sa.Column("progress_summary", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_weekly_reports_user_week", "weekly_reports", ["user_id", "report_week"])
    op.create_index("idx_weekly_reports_user_id", "weekly_reports", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_weekly_reports_user_id", "weekly_reports")
    op.drop_constraint("uq_weekly_reports_user_week", "weekly_reports")
    op.drop_table("weekly_reports")
