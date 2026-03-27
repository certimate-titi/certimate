"""Create exams, questions, answers tables.

Revision ID: 004
Revises: 003
Create Date: 2026-03-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute(sa.text("""
        DO $$ BEGIN CREATE TYPE exam_status AS ENUM ('PENDING', 'READY', 'IN_PROGRESS', 'SUBMITTED'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE question_type AS ENUM ('single_choice', 'multiple_choice', 'fill_in', 'calculation'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE difficulty_level AS ENUM ('easy', 'medium', 'hard'); EXCEPTION WHEN duplicate_object THEN null; END $$;
    """))

    # Create exams table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS exams (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject_id UUID NOT NULL REFERENCES subjects(id),
            institution_assignment_id UUID,
            status exam_status DEFAULT 'PENDING',
            total_questions INTEGER NOT NULL,
            duration_minutes INTEGER,
            passing_score INTEGER,
            difficulty_distribution JSONB,
            question_types TEXT[],
            score INTEGER,
            correct_count INTEGER,
            started_at TIMESTAMPTZ,
            submitted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """))

    # Create questions table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS questions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
            node_id UUID REFERENCES knowledge_nodes(id),
            question_number INTEGER NOT NULL,
            type question_type DEFAULT 'single_choice',
            difficulty difficulty_level DEFAULT 'medium',
            content TEXT NOT NULL,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_answer VARCHAR(10) NOT NULL,
            explanation TEXT,
            source_citation TEXT
        );
    """))

    # Create answers table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS answers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
            question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            selected_answer VARCHAR(10),
            is_correct BOOLEAN,
            marked_for_review BOOLEAN DEFAULT false,
            answered_at TIMESTAMPTZ,
            UNIQUE (exam_id, question_id, user_id)
        );
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS answers;"))
    op.execute(sa.text("DROP TABLE IF EXISTS questions;"))
    op.execute(sa.text("DROP TABLE IF EXISTS exams;"))
