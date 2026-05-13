"""scaffold_tags table — Feature 54 tags 3 sources 系統

Revision ID: 099
Revises: 098
Create Date: 2026-05-13
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "099"
down_revision = "098"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS scaffold_tags (
            scaffold_id     UUID        NOT NULL REFERENCES resource_scaffolds(id) ON DELETE CASCADE,
            user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tag_normalized  VARCHAR(64) NOT NULL,
            tag_display     VARCHAR(80) NOT NULL,
            CONSTRAINT pk_scaffold_tags PRIMARY KEY (scaffold_id, user_id, tag_normalized)
        );

        -- (user_id, tag_normalized) 複合 index，用於 cross-user filter
        CREATE INDEX IF NOT EXISTS ix_st_user_tag ON scaffold_tags (user_id, tag_normalized);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS scaffold_tags;
        """
    )
