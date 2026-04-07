"""Create prompt_templates_v2, prompt_template_versions, prompt_ab_tests tables.

Revision ID: 037
Revises: 036
Create Date: 2026-04-07

Feature 30: Prompt 模板管理
- 新增 prompt_templates_v2（取代舊版 prompt_templates schema）
- 新增 prompt_template_versions（版本歷史，取代舊 prompt_template_history）
- 新增 prompt_ab_tests（A/B 測試）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '037'
down_revision: Union[str, None] = '036'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ────────────────────────────────────────────────────────────────
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE prompt_category AS ENUM (
                'safety', 'knowledge', 'exam', 'teaching', 'emotion'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """))

    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE ab_test_status AS ENUM (
                'running', 'completed', 'cancelled'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """))

    # ── prompt_templates_v2 ──────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prompt_templates_v2 (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            template_id     VARCHAR(10) UNIQUE NOT NULL,
            name            VARCHAR(100) UNIQUE NOT NULL,
            display_name    VARCHAR(200) NOT NULL,
            category        prompt_category NOT NULL,
            model           VARCHAR(100) NOT NULL,
            max_tokens      INTEGER NOT NULL,
            max_tokens_by_plan JSONB,
            temperature     NUMERIC(2,1) NOT NULL DEFAULT 0.5,
            system_prompt   TEXT NOT NULL,
            user_prompt     TEXT NOT NULL,
            variables       JSONB NOT NULL DEFAULT '[]',
            feature_refs    TEXT[] DEFAULT '{}',
            current_version INTEGER NOT NULL DEFAULT 1,
            is_active       BOOLEAN NOT NULL DEFAULT true,
            created_by      UUID REFERENCES users(id),
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        );
    """))

    # ── prompt_template_versions ─────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prompt_template_versions (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            template_id         UUID NOT NULL
                                    REFERENCES prompt_templates_v2(id) ON DELETE CASCADE,
            version             INTEGER NOT NULL,
            model               VARCHAR(100) NOT NULL,
            max_tokens          INTEGER NOT NULL,
            max_tokens_by_plan  JSONB,
            temperature         NUMERIC(2,1) NOT NULL,
            system_prompt       TEXT NOT NULL,
            user_prompt         TEXT NOT NULL,
            variables           JSONB NOT NULL DEFAULT '[]',
            change_note         TEXT,
            created_by          UUID REFERENCES users(id),
            created_at          TIMESTAMPTZ DEFAULT now(),
            UNIQUE (template_id, version)
        );
    """))

    # ── prompt_ab_tests ──────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prompt_ab_tests (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            template_id             UUID NOT NULL
                                        REFERENCES prompt_templates_v2(id) ON DELETE CASCADE,
            name                    VARCHAR(200) NOT NULL,
            variant_a_version       INTEGER NOT NULL,
            variant_b_system_prompt TEXT NOT NULL,
            variant_b_user_prompt   TEXT NOT NULL,
            variant_b_temperature   NUMERIC(2,1),
            traffic_split           INTEGER NOT NULL DEFAULT 50,
            status                  ab_test_status DEFAULT 'running',
            metric_name             VARCHAR(100),
            variant_a_metric_value  NUMERIC(10,4),
            variant_b_metric_value  NUMERIC(10,4),
            winner                  VARCHAR(1),
            started_at              TIMESTAMPTZ DEFAULT now(),
            ended_at                TIMESTAMPTZ,
            created_by              UUID NOT NULL REFERENCES users(id),
            created_at              TIMESTAMPTZ DEFAULT now()
        );
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS prompt_ab_tests;"))
    op.execute(sa.text("DROP TABLE IF EXISTS prompt_template_versions;"))
    op.execute(sa.text("DROP TABLE IF EXISTS prompt_templates_v2;"))
    op.execute(sa.text("DROP TYPE IF EXISTS ab_test_status;"))
    op.execute(sa.text("DROP TYPE IF EXISTS prompt_category;"))
