"""Add question_order_mode to exams for interleaved practice (F19).

Revision ID: 075
Revises: 074
"""

from alembic import op
import sqlalchemy as sa


revision = "075"
down_revision = "074"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exams",
        sa.Column(
            "question_order_mode",
            sa.String(20),
            nullable=False,
            server_default="interleaved",
            comment="interleaved=交錯練習 / sequential=依難度排列 / grouped=集中練習",
        ),
    )


def downgrade() -> None:
    op.drop_column("exams", "question_order_mode")
