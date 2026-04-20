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
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "062"
down_revision = "061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Part A: subjects 加 owner_user_id + scope ---
    op.add_column(
        "subjects",
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "subjects",
        sa.Column(
            "scope",
            sa.String(20),
            nullable=False,
            server_default="platform",
        ),
    )
    op.create_index("ix_subjects_owner_scope", "subjects", ["owner_user_id", "scope"])

    # --- Part B: ResourceScope enum 加新值 ---
    # Postgres enum ADD VALUE 需獨立執行（不可在 transaction block 裡）
    # 用 CONNECTION.execution_options 繞過
    connection = op.get_bind()
    connection.execute(sa.text("COMMIT"))
    connection.execute(sa.text("ALTER TYPE resource_scope ADD VALUE IF NOT EXISTS 'platform'"))
    connection.execute(sa.text("ALTER TYPE resource_scope ADD VALUE IF NOT EXISTS 'shared'"))
    # 重新開啟 transaction
    connection.execute(sa.text("BEGIN"))

    # --- Part C: resources 加 target_institution_id ---
    op.add_column(
        "resources",
        sa.Column(
            "target_institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="SET NULL"),
            nullable=True,
            comment="scope=shared 時的分享目標 EDU 機構",
        ),
    )

    # --- Part D: subject_default_resources 關聯表 ---
    op.create_table(
        "subject_default_resources",
        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "resource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "added_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_subject_default_resources_subject",
        "subject_default_resources",
        ["subject_id"],
    )

    # --- Part E: Backfill platform subjects + system resources ---
    # 既有 28 個 seed subjects 已由 server_default='platform' 處理，scope 已正確
    # 只需確保 owner_user_id 為 NULL（預設就是 NULL）

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
    op.drop_index("ix_subject_default_resources_subject", table_name="subject_default_resources")
    op.drop_table("subject_default_resources")

    op.drop_column("resources", "target_institution_id")

    # Postgres 不支援移除 enum value，保留 platform / shared
    # 若需徹底回退需手動重建 type

    op.drop_index("ix_subjects_owner_scope", table_name="subjects")
    op.drop_column("subjects", "scope")
    op.drop_column("subjects", "owner_user_id")
