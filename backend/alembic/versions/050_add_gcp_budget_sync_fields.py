"""add gcp budget sync metadata fields to budget_config

Revision ID: 050
Revises: 049
Create Date: 2026-04-14

Feature 33 — GCP Native Budget 單向同步
新增 3 個欄位供應用層記錄與 GCP Billing Budgets API 的同步狀態。
"""

from alembic import op
import sqlalchemy as sa


revision = "050"
down_revision = "049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "budget_config",
        sa.Column(
            "gcp_budget_resource_name",
            sa.String(256),
            nullable=True,
            comment="對應的 GCP Budget resource name, e.g. billingAccounts/XXX/budgets/YYY",
        ),
    )
    op.add_column(
        "budget_config",
        sa.Column(
            "gcp_sync_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
            comment="是否啟用 GCP Native Budget 同步（AI_ANTHROPIC / AI_VOYAGE 應設為 false）",
        ),
    )
    op.add_column(
        "budget_config",
        sa.Column(
            "gcp_last_synced_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # AI_ANTHROPIC 與 AI_VOYAGE 不在 GCP 計費範圍，停用 GCP 同步
    op.execute(
        """
        UPDATE budget_config
        SET gcp_sync_enabled = false
        WHERE scope IN ('AI_ANTHROPIC', 'AI_VOYAGE')
        """
    )


def downgrade() -> None:
    op.drop_column("budget_config", "gcp_last_synced_at")
    op.drop_column("budget_config", "gcp_sync_enabled")
    op.drop_column("budget_config", "gcp_budget_resource_name")
