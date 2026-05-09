"""091 knowledge_nodes depth CHECK 1-3 — Sprint 10 T91.

教育顧問建議：節點分層放寬至 3 層彈性（章 / 節 / 子節）。
原本 prompt 限制 2 層，T89 已改 prompt + _save_knowledge_tree 寫第三層，
此 migration 加 DB 層約束防呆（避免未來改 ORM 時破壞此約定）。

對應 docs/ops/node-scaffold-pipeline-redesign-2026-05-09.md §10.2。
"""

from alembic import op


revision = "091"
down_revision = "090"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # depth 1=chapter / 2=section / 3=subsection（optional）
    # 既有資料 depth 都在 1-2，加約束安全；用 NOT VALID 先跳過驗證避免 long lock
    op.execute(
        "ALTER TABLE knowledge_nodes "
        "ADD CONSTRAINT chk_depth_range CHECK (depth BETWEEN 1 AND 3) NOT VALID"
    )
    # 確認既有資料都符合，再 VALIDATE（短鎖）
    op.execute(
        "ALTER TABLE knowledge_nodes VALIDATE CONSTRAINT chk_depth_range"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE knowledge_nodes DROP CONSTRAINT IF EXISTS chk_depth_range"
    )
