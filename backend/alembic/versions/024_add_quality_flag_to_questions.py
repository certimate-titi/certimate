"""add quality_flag and validation_result to questions

Revision ID: 024
Revises: 023
Create Date: 2026-04-03

Adds quality assurance fields for Cross-LLM validation.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("questions", sa.Column("quality_flag", sa.String(20), server_default="ok"))
    op.add_column("questions", sa.Column("flag_reason", sa.Text(), nullable=True))
    op.add_column("questions", sa.Column("flagged_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("questions", sa.Column("validation_model", sa.String(50), nullable=True))
    op.add_column("questions", sa.Column("validation_result", JSONB, nullable=True))


def downgrade():
    op.drop_column("questions", "validation_result")
    op.drop_column("questions", "validation_model")
    op.drop_column("questions", "flagged_at")
    op.drop_column("questions", "flag_reason")
    op.drop_column("questions", "quality_flag")
