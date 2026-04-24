"""Add reference_answer to resource_scaffolds (TASK-03).

Revision ID: 073
Revises: 072

EPIC MINDMAP-SCAFFOLD-INTEGRATION / TASK-03：
elaborative 類鷹架要在精讀模式顯示「AI 參考答案」作為第三步的比對素材。
採 pre-generate（寫入 DB）而非 on-demand，避免學生每次打開都等 LLM。
"""

from alembic import op
import sqlalchemy as sa


revision = "073"
down_revision = "072"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resource_scaffolds",
        sa.Column("reference_answer", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("resource_scaffolds", "reference_answer")
