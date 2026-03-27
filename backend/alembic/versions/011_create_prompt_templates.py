"""Create prompt_templates and prompt_template_history tables.

Revision ID: 011
Revises: 010
Create Date: 2026-03-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        DO $$ BEGIN CREATE TYPE prompt_stage_status AS ENUM ('active', 'inactive'); EXCEPTION WHEN duplicate_object THEN null; END $$;
    """))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prompt_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            stage_name VARCHAR(100) NOT NULL,
            stage_order INTEGER NOT NULL,
            status prompt_stage_status DEFAULT 'active',
            content TEXT,
            version INTEGER DEFAULT 1,
            modified_by VARCHAR(255),
            modified_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prompt_template_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            template_id UUID NOT NULL,
            version INTEGER NOT NULL,
            content TEXT,
            modified_by VARCHAR(255),
            modified_at TIMESTAMPTZ DEFAULT now()
        );
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS prompt_template_history;"))
    op.execute(sa.text("DROP TABLE IF EXISTS prompt_templates;"))
