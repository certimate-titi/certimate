"""Add parent_subject_id to subjects for hierarchical subject relationships.

Revision ID: 032
Revises: 031

Allows child subjects (e.g. '初級', '中級') to reference their parent subject,
replacing string-based name matching with a proper FK relationship.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "032"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "subjects",
        sa.Column("parent_subject_id", UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=True),
    )
    op.create_index("ix_subjects_parent_subject_id", "subjects", ["parent_subject_id"])


def downgrade():
    op.drop_index("ix_subjects_parent_subject_id", table_name="subjects")
    op.drop_column("subjects", "parent_subject_id")
