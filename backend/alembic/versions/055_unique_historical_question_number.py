"""Enforce UNIQUE (historical_exam_id, question_number) on questions table

Revision ID: 055
Revises: 054
Create Date: 2026-04-16

Root cause fix for the "只抓出 50 題" bug: questions table had no unique
constraint on (historical_exam_id, question_number), so re-running the
import_exam_questions script silently inserted duplicate rows. Over time,
some historical_exams accumulated 3x duplicates (e.g. FIN114 futures
analyst exams had 152 rows for 35 distinct questions).

Dedup was performed manually via SQL script before this migration runs.
This migration simply adds the constraint to prevent future recurrence.

The partial index ensures the constraint only applies to historical
questions (historical_exam_id IS NOT NULL) — regular exam questions
(exam_id IS NOT NULL, historical_exam_id IS NULL) can have arbitrary
question_numbers without clashing.
"""

from alembic import op


revision = "055"
down_revision = "054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_questions_historical_exam_q_number
        ON questions (historical_exam_id, question_number)
        WHERE historical_exam_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_questions_historical_exam_q_number")
