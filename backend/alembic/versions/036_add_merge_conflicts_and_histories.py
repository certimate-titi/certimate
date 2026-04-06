"""Add merge_conflicts and merge_histories tables for Feature 29.

Revision ID: 036
Revises: 035
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "merge_conflicts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("subject_id", UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("existing_node_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_nodes.id"), nullable=True),
        sa.Column("incoming_node_name", sa.String(255), nullable=False),
        sa.Column("similarity", sa.Numeric(5, 2), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending_review", nullable=False),
        sa.Column("suggestion", sa.String(30), nullable=True),
        sa.Column("resolution", sa.String(30), nullable=True),
        sa.Column("resolved_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "merge_histories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("subject_id", UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("trigger_source", sa.String(20), nullable=False),
        sa.Column("trigger_name", sa.String(255), nullable=True),
        sa.Column("nodes_added", sa.Integer, server_default="0"),
        sa.Column("nodes_merged", sa.Integer, server_default="0"),
        sa.Column("conflicts_count", sa.Integer, server_default="0"),
        sa.Column("merged_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("merge_histories")
    op.drop_table("merge_conflicts")
