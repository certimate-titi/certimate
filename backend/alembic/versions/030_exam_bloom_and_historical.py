"""Exam custom Bloom ratio and historical priority fields.

Revision ID: 030
Revises: 029
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("exams", sa.Column("custom_bloom_ratio", sa.JSON(), nullable=True))
    op.add_column("exams", sa.Column("historical_priority", sa.Boolean(), server_default=sa.text("false"), nullable=False))


def downgrade() -> None:
    op.drop_column("exams", "historical_priority")
    op.drop_column("exams", "custom_bloom_ratio")
