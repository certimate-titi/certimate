"""Add page_start / page_end to resource_scaffolds (TASK-02).

Revision ID: 072
Revises: 071

EPIC MINDMAP-SCAFFOLD-INTEGRATION / TASK-02：
鷹架卡原本只存 chapter_heading（自由字串），與 knowledge_nodes 沒有可靠映射鍵。
新增 page_start / page_end 後，可以用 [page_start, page_end] 與
knowledge_nodes.source_page_number 做區間比對，支援 node → scaffold mapping。
"""

from alembic import op
import sqlalchemy as sa


revision = "072"
down_revision = "071"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resource_scaffolds",
        sa.Column("page_start", sa.Integer, nullable=True),
    )
    op.add_column(
        "resource_scaffolds",
        sa.Column("page_end", sa.Integer, nullable=True),
    )
    op.create_index(
        "ix_resource_scaffolds_resource_pages",
        "resource_scaffolds",
        ["resource_id", "page_start", "page_end"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resource_scaffolds_resource_pages",
        table_name="resource_scaffolds",
    )
    op.drop_column("resource_scaffolds", "page_end")
    op.drop_column("resource_scaffolds", "page_start")
