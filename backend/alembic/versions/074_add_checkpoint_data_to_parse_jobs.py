"""Add checkpoint_data jsonb column to resource_parse_jobs.

Revision ID: 074
Revises: 073

Worker 處理 resource 時寫入 checkpoint，retry 時從 checkpoint resume。
欄位 schema：{"last_completed_step": "chunk|embed|knowledge|parse|merge", "step_data": {...}}
nullable + server_default='{}' 確保既有 row 不受影響。
"""

revision = "074"
down_revision = "073"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def upgrade() -> None:
    op.execute("""
        ALTER TABLE resource_parse_jobs
            ADD COLUMN IF NOT EXISTS checkpoint_data JSONB DEFAULT '{}'::jsonb
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE resource_parse_jobs
            DROP COLUMN IF EXISTS checkpoint_data
    """)
