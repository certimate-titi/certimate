"""Relax ck_questions_has_parent to allow source_resource_id (EPIC-035 personal bank).

Revision ID: 070
Revises: 069

Problem:
  migration 040 added CHECK (exam_id IS NOT NULL OR historical_exam_id IS NOT NULL),
  but EPIC-035 personal/user-upload questions attach to a Resource via
  source_resource_id, not an Exam/HistoricalExam. Those rows violated the check.

Fix:
  Replace with: exam_id IS NOT NULL OR historical_exam_id IS NOT NULL
              OR source_resource_id IS NOT NULL
"""

from alembic import op


revision = "070"
down_revision = "069"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_questions_has_parent", "questions", type_="check")
    op.create_check_constraint(
        "ck_questions_has_parent",
        "questions",
        "exam_id IS NOT NULL "
        "OR historical_exam_id IS NOT NULL "
        "OR source_resource_id IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_questions_has_parent", "questions", type_="check")
    op.create_check_constraint(
        "ck_questions_has_parent",
        "questions",
        "exam_id IS NOT NULL OR historical_exam_id IS NOT NULL",
    )
