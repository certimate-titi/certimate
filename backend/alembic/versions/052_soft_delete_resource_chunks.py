"""soft-delete resource_chunks + recompute strength trigger

Revision ID: 052
Revises: 051
Create Date: 2026-04-15

Mindmap architecture upgrade — T2-A 軟刪剪枝
- resource_chunks 新增 is_deleted 欄位（軟刪）
- 既有 hard-delete 改為 update is_deleted = true
- 搭配 MindmapStrengthService 自動重算節點強度，達成「優雅剪枝」效果
"""

from alembic import op
import sqlalchemy as sa


revision = "052"
down_revision = "051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resource_chunks",
        sa.Column(
            "is_deleted",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
            comment="軟刪標記 — true 時從檢索排除，供自動剪枝節點強度用",
        ),
    )
    op.add_column(
        "resource_chunks",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_resource_chunks_is_deleted",
        "resource_chunks",
        ["is_deleted"],
        postgresql_where=sa.text("is_deleted = false"),
    )


def downgrade() -> None:
    op.drop_index("idx_resource_chunks_is_deleted", table_name="resource_chunks")
    op.drop_column("resource_chunks", "deleted_at")
    op.drop_column("resource_chunks", "is_deleted")
