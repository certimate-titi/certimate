"""chat_message_annotations table + annotation_type enum

Revision ID: 095
Revises: 094
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "095"
down_revision = "094"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 使用 raw SQL 避免 SQLAlchemy Enum event 觸發 CREATE TYPE 競態
    op.execute(
        """
        DO $$
        BEGIN
            -- 1. Create annotation_type enum (idempotent)
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'annotation_type') THEN
                CREATE TYPE annotation_type AS ENUM (
                    'note',
                    'key_insight',
                    'challenge',
                    'example',
                    'application'
                );
            END IF;

            -- 2. Create chat_message_annotations table (idempotent)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'chat_message_annotations'
            ) THEN
                CREATE TABLE chat_message_annotations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    message_id UUID NOT NULL REFERENCES ai_chat_messages(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    session_id UUID NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,
                    highlighted_text TEXT NOT NULL,
                    user_annotation TEXT NOT NULL,
                    annotation_type annotation_type NOT NULL DEFAULT 'note',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT ck_cma_annotation_min_len CHECK (length(user_annotation) >= 10)
                );

                -- 3. Indexes
                CREATE INDEX ix_cma_user_id ON chat_message_annotations (user_id);
                CREATE INDEX ix_cma_message_id ON chat_message_annotations (message_id);
                CREATE INDEX ix_cma_session_id ON chat_message_annotations (session_id);
                CREATE INDEX ix_cma_user_recent ON chat_message_annotations (user_id, created_at);
                CREATE INDEX ix_cma_session_user ON chat_message_annotations (session_id, user_id);
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chat_message_annotations")
    op.execute("DROP TYPE IF EXISTS annotation_type")
