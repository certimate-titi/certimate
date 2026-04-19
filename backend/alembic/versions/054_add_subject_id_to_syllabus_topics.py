"""add subject_id to syllabus_topics (Feature 34 §3 Strategy E root solution)

Revision ID: 054
Revises: 053
Create Date: 2026-04-15

Link syllabus_topics to subjects so that the Strategy E cold-start anchor
mechanism can actually look up per-subject anchors. Previously the table had
only tenant_id + self-parent, which made it impossible to fetch "考綱錨點 for
subject X". This migration is the root fix for the 6-anchor-drift problem
that appears when data is sparse: with subject-scoped syllabus anchors,
UnifiedKnowledgeExtractionService can enforce "chapters must map to a
syllabus_topic", preventing LLM from hallucinating 6 out of thin air.

Changes:
- Add subject_id UUID NULL FK → subjects(id) ON DELETE CASCADE
- Index idx_syllabus_topics_subject (for per-subject lookups)

Nullable FK because the table may also host cross-subject / tenant-wide
meta topics in the future. Actual subject-scoped rows (written by seed
scripts) will always populate it.
"""

from alembic import op
import sqlalchemy as sa


revision = "054"
down_revision = "053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "syllabus_topics",
        sa.Column(
            "subject_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=True,
            comment="所屬科目（NULL = 跨科目 / 元數據）",
        ),
    )
    op.create_index(
        "idx_syllabus_topics_subject",
        "syllabus_topics",
        ["subject_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_syllabus_topics_subject", table_name="syllabus_topics")
    op.drop_column("syllabus_topics", "subject_id")
