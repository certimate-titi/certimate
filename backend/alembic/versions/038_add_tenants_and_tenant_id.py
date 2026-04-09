"""Add tenants table and tenant_id to key business tables.

Revision ID: 038
Revises: 037
Create Date: 2026-04-08

Phase 1 多租戶安全基礎建設：
- 新增 tenants 表（multi-tenant 隔離基礎）
- 新增預設租戶 public_b2c
- 在 resources, resource_chunks, questions, answers, exams 新增 tenant_id 欄位
- 為 tenant_id 建立索引（非強制 FK，以允許漸進式遷移）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "038"
down_revision = "037"
branch_labels = None
depends_on = None

# 預設租戶 UUID（固定值，供 seed 一致使用）
PUBLIC_B2C_TENANT_ID = "00000000-0000-0000-0000-000000b2cb2c"


def upgrade() -> None:
    # ── 1. 建立 tenants 表 ───────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(100), nullable=False, unique=True,
                  comment="唯一識別碼，如 public_b2c / institution_xyz"),
        sa.Column("name", sa.String(255), nullable=False,
                  comment="顯示名稱"),
        sa.Column("plan_tier", sa.String(50), nullable=False,
                  server_default="b2c",
                  comment="b2c | b2b_basic | b2b_pro | b2b_enterprise"),
        sa.Column("is_active", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.Column("max_users", sa.Integer(), nullable=True,
                  comment="B2B 授權人數上限，B2C 為 NULL"),
        sa.Column("storage_quota_bytes", sa.BigInteger(), nullable=True,
                  comment="儲存容量配額，NULL = 無限制"),
        sa.Column("llm_monthly_budget_usd", sa.Numeric(10, 2), nullable=True,
                  comment="每月 LLM 預算上限（美元），NULL = 無限制"),
        sa.Column("metadata_json", sa.JSON(), nullable=True,
                  comment="可擴充的租戶設定（白名單 domain, SSO config…）"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])
    op.create_index("ix_tenants_plan_tier", "tenants", ["plan_tier"])

    # ── 2. 植入預設 B2C 租戶 ────────────────────────────────────────────
    op.execute(
        sa.text(
            "INSERT INTO tenants (id, slug, name, plan_tier, is_active) "
            "VALUES (:id, 'public_b2c', '公開 B2C 平台', 'b2c', true) "
            "ON CONFLICT (slug) DO NOTHING"
        ).bindparams(sa.bindparam("id", type_=sa.UUID)
        ).params(id=PUBLIC_B2C_TENANT_ID)
    )

    # ── 3. 在業務表新增 tenant_id 欄位（可為 NULL，允許漸進式遷移）──────
    business_tables = [
        "resources",
        "resource_chunks",
        "questions",
        "answers",
        "exams",
        "knowledge_nodes",
        "ai_chat_sessions",
    ]
    for table in business_tables:
        op.add_column(
            table,
            sa.Column(
                "tenant_id",
                UUID(as_uuid=True),
                nullable=True,
                comment="多租戶隔離鍵（NULL = 歸屬 public_b2c）",
            ),
        )
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])

    # ── 4. 回填現有資料至 public_b2c 租戶 ───────────────────────────────
    for table in business_tables:
        op.execute(
            sa.text(
                f"UPDATE {table} SET tenant_id = :tid WHERE tenant_id IS NULL"
            ).bindparams(sa.bindparam("tid", type_=sa.UUID)
            ).params(tid=PUBLIC_B2C_TENANT_ID)
        )

    # ── 5. 啟用 PostgreSQL RLS（Row Level Security）──────────────────────
    # RLS 針對 resource_chunks（含向量資料）與 answers（含個資）強制啟用
    # app_user 為應用程式連線角色，需透過 SET LOCAL 傳入 tenant_id
    rls_tables = ["resource_chunks", "answers"]
    for table in rls_tables:
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        # Policy：只能看到自己租戶的資料（或使用 superuser bypass）
        op.execute(sa.text(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid "
            f"       OR current_setting('app.current_tenant_id', true) IS NULL)"
        ))


def downgrade() -> None:
    # 移除 RLS
    rls_tables = ["resource_chunks", "answers"]
    for table in rls_tables:
        op.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation ON {table}"))
        op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    # 移除 tenant_id 欄位
    business_tables = [
        "resources", "resource_chunks", "questions", "answers",
        "exams", "knowledge_nodes", "ai_chat_sessions",
    ]
    for table in business_tables:
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_column(table, "tenant_id")

    # 移除 tenants 表
    op.drop_index("ix_tenants_plan_tier", table_name="tenants")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
