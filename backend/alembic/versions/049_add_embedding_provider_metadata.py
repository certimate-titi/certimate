"""add embedding provider metadata + PENDING_BUDGET_RECOVERY status

Revision ID: 049
Revises: 048
Create Date: 2026-04-14

Feature 33 — 成本監控中心（前瞻性架構準備）
1. resource_chunks 新增 embedding_provider / embedding_model 欄位，
   為未來多 provider 並存（策略 C 雙軌向量庫）預留介面
2. resource_status enum 新增 PENDING_BUDGET_RECOVERY 值，
   用於 Voyage 達 80% 門檻時的降級佇列
"""

from alembic import op
import sqlalchemy as sa


revision = "049"
down_revision = "048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. resource_chunks 新增 embedding 中繼資料欄位
    # ------------------------------------------------------------------
    op.add_column(
        "resource_chunks",
        sa.Column(
            "embedding_provider",
            sa.String(32),
            nullable=False,
            server_default="voyage",
        ),
    )
    op.add_column(
        "resource_chunks",
        sa.Column(
            "embedding_model",
            sa.String(64),
            nullable=False,
            server_default="voyage-3",
        ),
    )
    op.create_index(
        "idx_resource_chunks_embedding_provider",
        "resource_chunks",
        ["embedding_provider"],
    )

    # ------------------------------------------------------------------
    # 2. resource_status enum 新增 PENDING_BUDGET_RECOVERY 值
    # ------------------------------------------------------------------
    op.execute(
        "ALTER TYPE resource_status ADD VALUE IF NOT EXISTS 'PENDING_BUDGET_RECOVERY'"
    )


def downgrade() -> None:
    # Postgres 不支援直接移除 enum value；此 downgrade 僅清除欄位
    op.drop_index(
        "idx_resource_chunks_embedding_provider", table_name="resource_chunks"
    )
    op.drop_column("resource_chunks", "embedding_model")
    op.drop_column("resource_chunks", "embedding_provider")
    # PENDING_BUDGET_RECOVERY enum 值保留於 resource_status type（不可逆）
