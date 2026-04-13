"""Add exam_subject_codes JSON column to subjects table.

Revision ID: 044
Revises: 043
Create Date: 2026-04-10

Stores the mapping from a subject to its historical exam codes,
enabling shared-subject resolution for civil service exams (高普考).

Example: ["114080:0102", "114080:0402", "114080:0302"]
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "044"
down_revision = "043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subjects",
        sa.Column("exam_subject_codes", JSONB, nullable=True, server_default=None),
    )


def downgrade() -> None:
    op.drop_column("subjects", "exam_subject_codes")
