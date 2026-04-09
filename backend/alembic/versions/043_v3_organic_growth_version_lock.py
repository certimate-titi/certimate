"""V3 有機生長：加入樂觀鎖 version 欄位.

Revision ID: 043
Revises: 042
Create Date: 2026-04-09

node_mastery 新增 version 欄位（樂觀鎖，防止併發覆寫）。
"""
from alembic import op
import sqlalchemy as sa

revision = "043"
down_revision = "042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("node_mastery", sa.Column(
        "version", sa.Integer(), server_default="1",
        comment="樂觀鎖版本號（V3 併發控制）",
    ))

    # 確保 mastery_rate 與 base_mastery 同步
    op.execute(sa.text("""
        UPDATE node_mastery SET mastery_rate = ROUND(CAST(base_mastery AS NUMERIC) * 100, 2)
        WHERE base_mastery > 0 AND (mastery_rate IS NULL OR mastery_rate = 0)
    """))


def downgrade() -> None:
    op.drop_column("node_mastery", "version")
