"""Create feedbacks and feedback_attachments tables.

Revision ID: 014
Revises: 013
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedbacks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("feedback_id", sa.String(50), unique=True, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("admin_reply", sa.Text),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("close_reason", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_feedback_user_id", "feedbacks", ["user_id"])
    op.create_index("idx_feedback_status", "feedbacks", ["status"])

    op.create_table(
        "feedback_attachments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("feedback_id", UUID(as_uuid=True), sa.ForeignKey("feedbacks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_feedback_attachment_feedback_id", "feedback_attachments", ["feedback_id"])


def downgrade() -> None:
    op.drop_index("idx_feedback_attachment_feedback_id", "feedback_attachments")
    op.drop_table("feedback_attachments")
    op.drop_index("idx_feedback_status", "feedbacks")
    op.drop_index("idx_feedback_user_id", "feedbacks")
    op.drop_table("feedbacks")
