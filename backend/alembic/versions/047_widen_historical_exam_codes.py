"""Widen historical_exams code columns from varchar(20) to varchar(50).

Revision ID: 047
Revises: 046
"""
from alembic import op
import sqlalchemy as sa

revision = "047"
down_revision = "046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("historical_exams", "exam_code", type_=sa.String(50), existing_type=sa.String(20))
    op.alter_column("historical_exams", "category_code", type_=sa.String(50), existing_type=sa.String(20))
    op.alter_column("historical_exams", "subject_code", type_=sa.String(50), existing_type=sa.String(20))


def downgrade() -> None:
    op.alter_column("historical_exams", "exam_code", type_=sa.String(20), existing_type=sa.String(50))
    op.alter_column("historical_exams", "category_code", type_=sa.String(20), existing_type=sa.String(50))
    op.alter_column("historical_exams", "subject_code", type_=sa.String(20), existing_type=sa.String(50))
