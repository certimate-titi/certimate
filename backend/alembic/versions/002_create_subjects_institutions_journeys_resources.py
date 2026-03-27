"""Create subject_categories, subjects, institutions, learning_journeys, resources tables.

Revision ID: 002
Revises: 001
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        DO $$ BEGIN CREATE TYPE resource_type AS ENUM ('pdf', 'markdown', 'txt', 'image', 'youtube'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE resource_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'COMPLETED_NO_MAP', 'FAILED'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE resource_scope AS ENUM ('personal', 'institution'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE learning_mode AS ENUM ('sprint', 'standard', 'mastery'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE self_assessed_level AS ENUM ('beginner', 'intermediate', 'advanced'); EXCEPTION WHEN duplicate_object THEN null; END $$;
    """))

    op.execute(sa.text("""
        CREATE TABLE subject_categories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(50) NOT NULL,
            sort_order INTEGER DEFAULT 0
        );
    """))

    op.execute(sa.text("""
        CREATE TABLE subjects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            category_id UUID NOT NULL REFERENCES subject_categories(id),
            name VARCHAR(200) NOT NULL,
            name_en VARCHAR(200),
            description TEXT,
            is_popular BOOLEAN DEFAULT false,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """))

    op.execute(sa.text("""
        CREATE TABLE institutions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(200) NOT NULL,
            admin_user_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """))

    op.execute(sa.text("""
        CREATE TABLE learning_journeys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject_id UUID NOT NULL REFERENCES subjects(id),
            exam_date DATE,
            self_assessed_level self_assessed_level DEFAULT 'beginner',
            learning_mode learning_mode DEFAULT 'standard',
            is_archived BOOLEAN DEFAULT false,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE (user_id, subject_id)
        );
    """))

    op.execute(sa.text("""
        CREATE TABLE resources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject_id UUID NOT NULL REFERENCES subjects(id),
            institution_id UUID REFERENCES institutions(id),
            name VARCHAR(500) NOT NULL,
            type resource_type NOT NULL,
            scope resource_scope DEFAULT 'personal',
            status resource_status DEFAULT 'PENDING',
            file_size_bytes BIGINT,
            gcs_path TEXT,
            youtube_url TEXT,
            processing_engine VARCHAR(50),
            implicit_consent BOOLEAN DEFAULT true,
            tags TEXT[] DEFAULT '{}',
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DROP TABLE IF EXISTS resources;
        DROP TABLE IF EXISTS learning_journeys;
        DROP TABLE IF EXISTS institutions;
        DROP TABLE IF EXISTS subjects;
        DROP TABLE IF EXISTS subject_categories;
        DROP TYPE IF EXISTS self_assessed_level;
        DROP TYPE IF EXISTS learning_mode;
        DROP TYPE IF EXISTS resource_scope;
        DROP TYPE IF EXISTS resource_status;
        DROP TYPE IF EXISTS resource_type;
    """))
