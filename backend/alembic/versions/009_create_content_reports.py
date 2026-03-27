"""009 create content_reports table

Revision ID: 009
Revises: 008
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_reports",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("report_ref", sa.String(50), unique=True, nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("resolution_action", sa.String(50)),
        sa.Column("resolution_note", sa.Text()),
        sa.Column("resolved_by", sa.String(50)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("content_reports")
