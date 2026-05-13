"""chat_annotation_tags table — Feature 54 tags 3 sources 系統

Revision ID: 098
Revises: 097
Create Date: 2026-05-13
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "098"
down_revision = "097"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_annotation_tags (
            annotation_id   UUID        NOT NULL REFERENCES chat_message_annotations(id) ON DELETE CASCADE,
            tag_normalized  VARCHAR(64) NOT NULL,
            tag_display     VARCHAR(80) NOT NULL,
            CONSTRAINT pk_chat_annotation_tags PRIMARY KEY (annotation_id, tag_normalized)
        );

        CREATE INDEX IF NOT EXISTS ix_cat_annotation ON chat_annotation_tags (annotation_id);
        CREATE INDEX IF NOT EXISTS ix_cat_tag        ON chat_annotation_tags (tag_normalized);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS chat_annotation_tags;
        """
    )
