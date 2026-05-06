"""Add 'final' value to learning_mode enum + restructure 4-phase timeline.

業務變動：3 階段 → 4 階段
- mastery: > 180 天（不變）
- standard: 31-180 天（改：原 15-180）
- sprint: 8-30 天（改：原 ≤14）
- final: ≤ 7 天（新增）

Revision ID: 079
Revises: 078
"""

from alembic import op


revision = "079"
down_revision = "078"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL enum 加值（無法刪舊值，但可加新值）
    op.execute(
        """
        DO $$ BEGIN
            ALTER TYPE learning_mode ADD VALUE IF NOT EXISTS 'final';
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
        """
    )


def downgrade() -> None:
    # PostgreSQL 不支援移除 enum value；降級時把 'final' 回填為 'sprint'
    op.execute(
        """
        UPDATE learning_journeys SET learning_mode = 'sprint'
        WHERE learning_mode = 'final';
        """
    )
    # 留 enum value 不做（PG 限制）
