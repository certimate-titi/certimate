"""Expand prompt_templates_v2.template_id from VARCHAR(10) to VARCHAR(32).

Sprint 4 P3 T38：原 VARCHAR(10) 太短，無法容納 K-06-slides / K-06-video
等新模板 ID。擴到 VARCHAR(32) 以支援未來模板分流命名。

Revision ID: 085
Revises: 084
"""

from alembic import op
import sqlalchemy as sa

revision = "085"
down_revision = "084"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "prompt_templates_v2",
        "template_id",
        type_=sa.String(32),
        existing_type=sa.String(10),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "prompt_templates_v2",
        "template_id",
        type_=sa.String(10),
        existing_type=sa.String(32),
        existing_nullable=False,
    )
