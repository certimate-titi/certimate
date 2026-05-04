"""Add notification_preferences JSON column to users (F22).

L81：/account 通知偏好原本只存 localStorage，落地至 user.notification_preferences。

Revision ID: 076
Revises: 075
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "076"
down_revision = "075"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "notification_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment="F22 通知偏好（daily_reminder / pre_exam_reminder / weekly_report 等開關）",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "notification_preferences")
