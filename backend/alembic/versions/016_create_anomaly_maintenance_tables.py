"""Create anomaly_records, maintenance_tasks, maintenance_schedules, maintenance_notifications tables.

Revision ID: 016
Revises: 015
Create Date: 2026-03-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # anomaly_records
    op.create_table(
        "anomaly_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("error_id", sa.String(50), unique=True, nullable=False),
        sa.Column("error_type", sa.String(200), nullable=False),
        sa.Column("occurrence_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("impact_scope", sa.String(100), nullable=False),
        sa.Column("assigned_to", sa.String(200)),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # maintenance_tasks
    op.create_table(
        "maintenance_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("task_id", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("related_error_id", UUID(as_uuid=True), sa.ForeignKey("anomaly_records.id")),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("estimated_hours", sa.Numeric(5, 1)),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_to", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # maintenance_schedules
    op.create_table(
        "maintenance_schedules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notify_channels", ARRAY(sa.String), server_default="{}"),
        sa.Column("notify_targets", sa.String(100)),
        sa.Column("notify_before", ARRAY(sa.String), server_default="{}"),
        sa.Column("reason", sa.Text),
        sa.Column("is_full_site", sa.Boolean, server_default="false"),
        sa.Column("health_check_passed", sa.Boolean, server_default="false"),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # maintenance_notifications
    op.create_table(
        "maintenance_notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("schedule_id", UUID(as_uuid=True), sa.ForeignKey("maintenance_schedules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_send_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("maintenance_notifications")
    op.drop_table("maintenance_schedules")
    op.drop_table("maintenance_tasks")
    op.drop_table("anomaly_records")
