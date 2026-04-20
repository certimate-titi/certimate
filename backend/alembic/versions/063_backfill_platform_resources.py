"""Backfill: mark system@certimate.app 考古題 resources as scope=platform + bind as defaults.

Revision ID: 063
Revises: 062

Context:
- Migration 062 added 'platform' enum value but cannot use it in the same transaction.
- This migration runs the backfill in a fresh transaction.
- Idempotent: safe to rerun; ON CONFLICT DO NOTHING on subject_default_resources.
"""

from alembic import op
import sqlalchemy as sa


revision = "063"
down_revision = "062"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alembic 將連續 migration 包在同一 transaction；在這裡強制 COMMIT
    # 讓 062 加的 'platform' / 'shared' enum 值進入新 transaction 後安全可用
    connection = op.get_bind()
    connection.execute(sa.text("COMMIT"))
    connection.execute(sa.text("BEGIN"))

    # system@certimate.app 的「考古題題庫」resources → scope=platform
    op.execute("""
        UPDATE resources
        SET scope = 'platform'
        WHERE user_id IN (SELECT id FROM users WHERE email = 'system@certimate.app')
          AND name LIKE '%考古題題庫%'
          AND scope != 'platform'
    """)

    # 寫入 subject_default_resources 關聯表
    op.execute("""
        INSERT INTO subject_default_resources (subject_id, resource_id, added_by_user_id)
        SELECT r.subject_id, r.id, r.user_id
        FROM resources r
        JOIN users u ON u.id = r.user_id
        WHERE u.email = 'system@certimate.app'
          AND r.scope = 'platform'
          AND r.subject_id IS NOT NULL
        ON CONFLICT (subject_id, resource_id) DO NOTHING
    """)


def downgrade() -> None:
    # 不反向操作（保留 platform 標記）
    pass
