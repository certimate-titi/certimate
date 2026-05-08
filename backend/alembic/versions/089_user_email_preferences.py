"""089 user_email_preferences + email_send_log — Sprint 9 議題 E.

Retention email 系統的兩張表：
- user_email_preferences：每用戶 4 個 email 開關（事務型 parse_failure 強制 enabled）
  + unsubscribe_token JWT
- email_send_log：每次寄送結果（24h 重寄防護 + A/B 指標彙總）
"""

from alembic import op
import sqlalchemy as sa


revision = "089"
down_revision = "088"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_email_preferences",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("daily_review_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("weekly_report_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("streak_warning_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("parse_failure_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("unsubscribe_token", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "email_send_log",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),  # sent / skipped / failed
        sa.Column("reason", sa.String(255)),
        sa.Column("subject_variant", sa.String(8)),  # A / B
        sa.Column("subject", sa.String(255)),
        sa.Column("sent_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_email_send_log_user_trigger_sent",
        "email_send_log",
        ["user_id", "trigger_id", "sent_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_email_send_log_user_trigger_sent", table_name="email_send_log")
    op.drop_table("email_send_log")
    op.drop_table("user_email_preferences")
