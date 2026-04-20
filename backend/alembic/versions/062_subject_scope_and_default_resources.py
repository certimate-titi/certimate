"""Subject scope + owner + default resources + ResourceScope enum expansion.

Revision ID: 062
Revises: 061

Context (PRD-033 §6.2):
- subjects 加 owner_user_id + scope → 支援用戶自建考科（scope=personal）和平台官方（scope=platform）
- ResourceScope enum 加 platform (所有用戶可見) + shared (Ultra → EDU 分享)
- resources 加 target_institution_id (scope=shared 時的分享目標)
- 新建 subject_default_resources 關聯表 (平台預設資源綁定機制)
- Backfill:
  - 28 個 seed subjects → scope=platform, owner_user_id=NULL
  - system@certimate.app 用戶的 5 筆「考古題題庫」resources → scope=platform + 寫入關聯表

冪等性：所有 DDL 使用 IF NOT EXISTS，以支援部分失敗後重跑。
"""

from alembic import op
import sqlalchemy as sa


revision = "062"
down_revision = "061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Part A: subjects 加 owner_user_id + scope (冪等) ---
    op.execute("""
        ALTER TABLE subjects
            ADD COLUMN IF NOT EXISTS owner_user_id UUID REFERENCES users(id) ON DELETE CASCADE
    """)
    op.execute("""
        ALTER TABLE subjects
            ADD COLUMN IF NOT EXISTS scope VARCHAR(20) NOT NULL DEFAULT 'platform'
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_subjects_owner_scope
            ON subjects (owner_user_id, scope)
    """)

    # --- Part B: ResourceScope enum 加新值 ---
    # Postgres enum ADD VALUE 需在自己的 transaction；這裡用 IF NOT EXISTS 所以可重跑
    connection = op.get_bind()
    connection.execute(sa.text("COMMIT"))
    connection.execute(sa.text("ALTER TYPE resource_scope ADD VALUE IF NOT EXISTS 'platform'"))
    connection.execute(sa.text("ALTER TYPE resource_scope ADD VALUE IF NOT EXISTS 'shared'"))
    connection.execute(sa.text("BEGIN"))

    # --- Part C: resources 加 target_institution_id (冪等) ---
    op.execute("""
        ALTER TABLE resources
            ADD COLUMN IF NOT EXISTS target_institution_id UUID
                REFERENCES institutions(id) ON DELETE SET NULL
    """)
    op.execute("""
        COMMENT ON COLUMN resources.target_institution_id IS 'scope=shared 時的分享目標 EDU 機構'
    """)

    # --- Part D: subject_default_resources 關聯表 (冪等) ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS subject_default_resources (
            subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
            added_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            added_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            PRIMARY KEY (subject_id, resource_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_subject_default_resources_subject
            ON subject_default_resources (subject_id)
    """)

    # --- Part E: Backfill ---
    # system@certimate.app 5 筆「考古題題庫」resources → scope=platform
    op.execute("""
        UPDATE resources
        SET scope = 'platform'
        WHERE user_id IN (SELECT id FROM users WHERE email = 'system@certimate.app')
          AND name LIKE '%考古題題庫%'
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
    op.execute("DROP INDEX IF EXISTS ix_subject_default_resources_subject")
    op.execute("DROP TABLE IF EXISTS subject_default_resources")
    op.execute("ALTER TABLE resources DROP COLUMN IF EXISTS target_institution_id")
    op.execute("DROP INDEX IF EXISTS ix_subjects_owner_scope")
    op.execute("ALTER TABLE subjects DROP COLUMN IF EXISTS scope")
    op.execute("ALTER TABLE subjects DROP COLUMN IF EXISTS owner_user_id")
