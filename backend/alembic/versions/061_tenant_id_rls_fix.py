"""Fix RLS policy (tolerate empty string GUC) + backfill NULL tenant_id + set column DEFAULT.

Revision ID: 061
Revises: 060

Context:
- Migration 038 added tenant_id columns but application layer never populates them
- resource_chunks / answers RLS policy uses `current_setting(...)::uuid` which crashes
  when GUC is set to empty string (not NULL, not UUID)
- 5 tables have 100% NULL tenant_id rows that need backfill

Scope:
- Fix RLS policy on resource_chunks + answers (tolerate '' and NULL)
- Backfill 5 tables (resources, resource_chunks, knowledge_nodes, exams, syllabus_topics)
- Set DEFAULT on tenant_id columns so future INSERTs without explicit value land on PUBLIC_B2C

See PRD-033 §6.1.
"""

from alembic import op


revision = "061"
down_revision = "060"
branch_labels = None
depends_on = None


PUBLIC_B2C_TENANT_ID = "00000000-0000-0000-0000-000000b2cb2c"

TENANT_TABLES = [
    "resources",
    "resource_chunks",
    "knowledge_nodes",
    "exams",
    "syllabus_topics",
]

RLS_TABLES = ["resource_chunks", "answers"]


def upgrade() -> None:
    # --- Part A: Backfill NULL tenant_id ---
    for table in TENANT_TABLES:
        op.execute(
            f"UPDATE {table} SET tenant_id = '{PUBLIC_B2C_TENANT_ID}'::uuid "
            f"WHERE tenant_id IS NULL"
        )

    # --- Part B: Set DEFAULT on tenant_id columns ---
    for table in TENANT_TABLES:
        op.execute(
            f"ALTER TABLE {table} "
            f"ALTER COLUMN tenant_id SET DEFAULT '{PUBLIC_B2C_TENANT_ID}'::uuid"
        )

    # --- Part C: Fix RLS policy to tolerate empty string GUC ---
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} USING ("
            f"  current_setting('app.current_tenant_id', true) IS NULL"
            f"  OR current_setting('app.current_tenant_id', true) = ''"
            f"  OR tenant_id = (current_setting('app.current_tenant_id', true))::uuid"
            f")"
        )


def downgrade() -> None:
    # Restore original RLS policy (without empty-string tolerance)
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} USING ("
            f"  tenant_id = (current_setting('app.current_tenant_id', true))::uuid"
            f"  OR current_setting('app.current_tenant_id', true) IS NULL"
            f")"
        )

    # Drop DEFAULT
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id DROP DEFAULT")

    # Note: backfilled data not reverted (unsafe to NULL them back)
