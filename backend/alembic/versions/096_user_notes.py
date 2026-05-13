"""user_notes table — Feature 50 我的筆記整合

Revision ID: 096
Revises: 095
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "096"
down_revision = "095"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_notes (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject_id  UUID        NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            node_id     UUID        REFERENCES knowledge_nodes(id) ON DELETE SET NULL,
            title       VARCHAR(200),
            content     TEXT        NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_un_content_not_empty CHECK (length(content) > 0)
        );

        -- indexes
        CREATE INDEX IF NOT EXISTS ix_un_user          ON user_notes (user_id);
        CREATE INDEX IF NOT EXISTS ix_un_user_subject  ON user_notes (user_id, subject_id);
        CREATE INDEX IF NOT EXISTS ix_un_user_node     ON user_notes (user_id, node_id);
        CREATE INDEX IF NOT EXISTS ix_un_user_recent   ON user_notes (user_id, updated_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS user_notes;
        """
    )
