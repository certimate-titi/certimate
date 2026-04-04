"""031 create institution_assignments and early_warning_rules tables

Revision ID: 031
Revises: 030
Create Date: 2026-04-04
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from alembic import op

revision = "031"
down_revision = "030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institution_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("institution_id", UUID(as_uuid=True), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("group_id", UUID(as_uuid=True), sa.ForeignKey("student_groups.id"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("exam_config", JSONB, nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "early_warning_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("institution_id", UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("min_avg_score", sa.Numeric(5, 2), server_default="60"),
        sa.Column("max_decline_trend", sa.Integer, server_default="3"),
        sa.Column("max_inactive_days", sa.Integer, server_default="5"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("early_warning_rules")
    op.drop_table("institution_assignments")
    op.execute(sa.text("DROP TYPE IF EXISTS assignment_status"))
