"""add cost monitor tables (ai_usage_ledger, budget_config, budget_alert_log)

Revision ID: 048
Revises: 047
Create Date: 2026-04-14

Feature 33 — 成本監控中心
新增三張表支援 AI 供應商與 GCP 成本追蹤、預算管理與告警歷史。
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "048"
down_revision = "047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # ai_usage_ledger — AI 呼叫 token 級明細
    # ------------------------------------------------------------------
    op.create_table(
        "ai_usage_ledger",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("endpoint", sa.String(128), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "cost_usd",
            sa.Numeric(12, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "billing_source",
            sa.String(16),
            nullable=False,
            server_default="app",
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("feature", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_ai_usage_ledger_provider_date",
        "ai_usage_ledger",
        ["provider", "created_at"],
    )
    op.create_index(
        "idx_ai_usage_ledger_created_at",
        "ai_usage_ledger",
        ["created_at"],
    )
    op.create_index(
        "idx_ai_usage_ledger_user_id",
        "ai_usage_ledger",
        ["user_id"],
    )

    # ------------------------------------------------------------------
    # budget_config — 預算設定與當前狀態
    # ------------------------------------------------------------------
    op.create_table(
        "budget_config",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("scope", sa.String(32), nullable=False, unique=True),
        sa.Column("monthly_limit_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "warning_percent", sa.Integer, nullable=False, server_default="50"
        ),
        sa.Column(
            "degrade_percent", sa.Integer, nullable=False, server_default="80"
        ),
        sa.Column(
            "disable_percent", sa.Integer, nullable=False, server_default="100"
        ),
        sa.Column(
            "current_state",
            sa.String(16),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "overridden_until", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "warning_percent >= 1 AND warning_percent <= 100",
            name="ck_budget_config_warning_percent",
        ),
        sa.CheckConstraint(
            "degrade_percent >= 1 AND degrade_percent <= 100",
            name="ck_budget_config_degrade_percent",
        ),
        sa.CheckConstraint(
            "disable_percent >= 1 AND disable_percent <= 100",
            name="ck_budget_config_disable_percent",
        ),
        sa.CheckConstraint(
            "warning_percent < degrade_percent AND degrade_percent <= disable_percent",
            name="ck_budget_config_threshold_order",
        ),
        sa.CheckConstraint(
            "current_state IN ('active','warning','degraded','disabled')",
            name="ck_budget_config_current_state",
        ),
        sa.CheckConstraint(
            "scope IN ('AI_ANTHROPIC','AI_GEMINI','AI_VOYAGE','GCP_TOTAL')",
            name="ck_budget_config_scope",
        ),
    )

    # ------------------------------------------------------------------
    # budget_alert_log — 告警歷史
    # ------------------------------------------------------------------
    op.create_table(
        "budget_alert_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("scope", sa.String(32), nullable=False),
        sa.Column("alert_type", sa.String(16), nullable=False),
        sa.Column("triggered_at_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("limit_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("percent", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "notified_channels", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "alert_type IN ('WARNING','DEGRADE','DISABLED')",
            name="ck_budget_alert_log_alert_type",
        ),
    )
    op.create_index(
        "idx_budget_alert_log_scope_date",
        "budget_alert_log",
        ["scope", "created_at"],
    )

    # ------------------------------------------------------------------
    # Seed 預算設定（依財務建議）
    # ------------------------------------------------------------------
    op.execute(
        """
        INSERT INTO budget_config (scope, monthly_limit_usd, warning_percent, degrade_percent, disable_percent)
        VALUES
            ('AI_ANTHROPIC', 700.00, 50, 80, 100),
            ('AI_GEMINI',    100.00, 50, 80, 100),
            ('AI_VOYAGE',     50.00, 50, 80, 100),
            ('GCP_TOTAL',    400.00, 50, 80, 100)
        ON CONFLICT (scope) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("idx_budget_alert_log_scope_date", table_name="budget_alert_log")
    op.drop_table("budget_alert_log")

    op.drop_table("budget_config")

    op.drop_index("idx_ai_usage_ledger_user_id", table_name="ai_usage_ledger")
    op.drop_index("idx_ai_usage_ledger_created_at", table_name="ai_usage_ledger")
    op.drop_index(
        "idx_ai_usage_ledger_provider_date", table_name="ai_usage_ledger"
    )
    op.drop_table("ai_usage_ledger")
