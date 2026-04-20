"""PRD-034 platform subject fork model.

Revision ID: 065
Revises: 064

- subjects: add source_platform_subject_id, version, published_at
- knowledge_nodes: add source_resource_count (引用計數，cascade 刪除用)
- Backfill: existing platform subjects get version=1, published_at=now();
  existing knowledge_nodes get source_resource_count=1.

Idempotent: all DDL uses IF NOT EXISTS / IF EXISTS.
"""

from alembic import op


revision = "065"
down_revision = "064"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE subjects
            ADD COLUMN IF NOT EXISTS source_platform_subject_id UUID
                REFERENCES subjects(id) ON DELETE SET NULL
    """)
    op.execute("""
        ALTER TABLE subjects
            ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1
    """)
    op.execute("""
        ALTER TABLE subjects
            ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ
    """)
    # Platform subjects: mark as published now (first-time migration)
    op.execute("""
        UPDATE subjects
        SET published_at = COALESCE(published_at, now())
        WHERE scope = 'platform' AND published_at IS NULL
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_subjects_source_platform_subject_id
            ON subjects (source_platform_subject_id)
    """)

    op.execute("""
        ALTER TABLE knowledge_nodes
            ADD COLUMN IF NOT EXISTS source_resource_count INTEGER NOT NULL DEFAULT 1
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_subjects_source_platform_subject_id")
    op.execute("ALTER TABLE subjects DROP COLUMN IF EXISTS published_at")
    op.execute("ALTER TABLE subjects DROP COLUMN IF EXISTS version")
    op.execute("ALTER TABLE subjects DROP COLUMN IF EXISTS source_platform_subject_id")
    op.execute("ALTER TABLE knowledge_nodes DROP COLUMN IF EXISTS source_resource_count")
