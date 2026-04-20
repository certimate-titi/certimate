"""RLS policy defensive rewrite using NULLIF to guarantee empty-string GUC tolerance.

Revision ID: 064
Revises: 063

Context:
- Migration 061 added empty-string tolerance via `OR current_setting = ''` branch.
- Cloud still observes `invalid input syntax for type uuid: ""` on resource_chunks
  and answers (same table set as 061). Root cause is unclear — 061 appears applied
  per alembic_version, but cloud planner still evaluates the ::uuid cast branch.
- This migration rewrites the policy to NEVER cast empty string to uuid, using
  NULLIF(current_setting(...), '') which returns NULL for empty strings.
  Comparing `tenant_id = NULL::uuid` is NULL (not TRUE), so the row is filtered —
  but the `IS NULL` branch catches the "no tenant set" case.

- Idempotent: DROP POLICY IF EXISTS then CREATE.
"""

from alembic import op


revision = "064"
down_revision = "063"
branch_labels = None
depends_on = None


RLS_TABLES = ["resource_chunks", "answers"]


def upgrade() -> None:
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} USING ("
            f"  NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL"
            f"  OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"
            f")"
        )


def downgrade() -> None:
    # Restore 061's policy shape
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} USING ("
            f"  current_setting('app.current_tenant_id', true) IS NULL"
            f"  OR current_setting('app.current_tenant_id', true) = ''"
            f"  OR tenant_id = (current_setting('app.current_tenant_id', true))::uuid"
            f")"
        )
