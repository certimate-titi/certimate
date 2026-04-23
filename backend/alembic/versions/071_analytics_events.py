"""Create analytics_events table (PRD-046 US-07).

Revision ID: 071
Revises: 070

Stores frontend analytics events flushed from the localStorage queue.
Retention: 90 days (enforced by application / cron; no DB-level TTL).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "071"
down_revision = "070"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("props", JSONB, nullable=True),
        sa.Column("client_ts", sa.BigInteger, nullable=False, comment="客戶端時間戳 (ms)"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_analytics_events_name_ts", "analytics_events", ["name", "created_at"])
    op.create_index("ix_analytics_events_user_ts", "analytics_events", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_analytics_events_user_ts", table_name="analytics_events")
    op.drop_index("ix_analytics_events_name_ts", table_name="analytics_events")
    op.drop_table("analytics_events")
