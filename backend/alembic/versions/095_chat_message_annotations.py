"""chat_message_annotations table + annotation_type enum

Revision ID: 095
Revises: 094
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "095"
down_revision = "094"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create enum type
    op.execute(
        """
        CREATE TYPE annotation_type AS ENUM (
            'note',
            'key_insight',
            'challenge',
            'example',
            'application'
        )
        """
    )

    # 2. Create table
    op.create_table(
        "chat_message_annotations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("message_id", UUID(as_uuid=True), sa.ForeignKey("ai_chat_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("highlighted_text", sa.Text, nullable=False),
        sa.Column("user_annotation", sa.Text, nullable=False),
        sa.Column(
            "annotation_type",
            sa.Enum(
                "note", "key_insight", "challenge", "example", "application",
                name="annotation_type",
                create_type=False,
            ),
            nullable=False,
            server_default="note",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("length(user_annotation) >= 10", name="ck_cma_annotation_min_len"),
    )

    # 3. Indexes
    op.create_index("ix_cma_user_id", "chat_message_annotations", ["user_id"])
    op.create_index("ix_cma_message_id", "chat_message_annotations", ["message_id"])
    op.create_index("ix_cma_session_id", "chat_message_annotations", ["session_id"])
    op.create_index("ix_cma_user_recent", "chat_message_annotations", ["user_id", "created_at"])
    op.create_index("ix_cma_session_user", "chat_message_annotations", ["session_id", "user_id"])


def downgrade() -> None:
    op.drop_table("chat_message_annotations")
    op.execute("DROP TYPE IF EXISTS annotation_type")
