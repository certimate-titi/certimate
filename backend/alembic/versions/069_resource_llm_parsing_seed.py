"""Seed per-plan monthly_resource_parse_limit quotas (EPIC-035).

Revision ID: 069
Revises: 068

Idempotent UPSERT: plan_quotas rows may already exist (from earlier seeds).
  FREE        → 5
  PRO         → 50
  PRO_PLUS    → 200
  ULTRA       → -1 (無限)

Prompt Template `resource_parser_v2` 由 seed 腳本寫入（非 migration）。
"""

from alembic import op


revision = "069"
down_revision = "068"
branch_labels = None
depends_on = None


QUOTAS = [
    ("FREE", 5),
    ("PRO", 50),
    ("PRO_PLUS", 200),
    ("ULTRA", -1),
]


def upgrade() -> None:
    for plan, limit in QUOTAS:
        op.execute(f"""
            INSERT INTO plan_quotas (plan, monthly_resource_parse_limit, updated_at)
            VALUES ('{plan}', {limit}, NOW())
            ON CONFLICT (plan) DO UPDATE
                SET monthly_resource_parse_limit = EXCLUDED.monthly_resource_parse_limit,
                    updated_at = NOW()
        """)


def downgrade() -> None:
    op.execute("UPDATE plan_quotas SET monthly_resource_parse_limit = NULL")
