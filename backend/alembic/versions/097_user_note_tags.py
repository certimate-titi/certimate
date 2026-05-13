"""user_note_tags table — Feature 52 筆記 hashtag 系統

Revision ID: 097
Revises: 096
Create Date: 2026-05-13
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "097"
down_revision = "096"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_note_tags (
            note_id         UUID        NOT NULL REFERENCES user_notes(id) ON DELETE CASCADE,
            tag_normalized  VARCHAR(64) NOT NULL,
            tag_display     VARCHAR(80) NOT NULL,
            CONSTRAINT pk_user_note_tags PRIMARY KEY (note_id, tag_normalized)
        );

        -- indexes
        CREATE INDEX IF NOT EXISTS ix_unt_note ON user_note_tags (note_id);
        CREATE INDEX IF NOT EXISTS ix_unt_tag  ON user_note_tags (tag_normalized);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS user_note_tags;
        """
    )
