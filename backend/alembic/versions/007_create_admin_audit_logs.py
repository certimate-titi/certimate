"""Create admin_audit_logs table.

Revision ID: 007
Revises: 006
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("admin_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50)),
        sa.Column("target_id", UUID(as_uuid=True)),
        sa.Column("details", JSONB),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("user_agent", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_admin", "admin_audit_logs", ["admin_id"])
    op.create_index("idx_audit_action", "admin_audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("idx_audit_action", "admin_audit_logs")
    op.drop_index("idx_audit_admin", "admin_audit_logs")
    op.drop_table("admin_audit_logs")
