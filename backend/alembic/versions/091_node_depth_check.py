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
    # 修正歷史資料：早期 default=0 的 root node 改為 1（chapter 層）
    op.execute(
        "UPDATE knowledge_nodes SET depth = 1 WHERE depth = 0 AND parent_id IS NULL"
    )
    # 防呆：parent_id 不為 NULL 但 depth=0 的視為 section（depth=2）
    op.execute(
        "UPDATE knowledge_nodes SET depth = 2 WHERE depth = 0 AND parent_id IS NOT NULL"
    )
    # 不 VALIDATE — NOT VALID constraint 對未來寫入仍有效（防呆）
    # 既有資料若 cleanup 後仍有 depth>3 的（不應發生），保留 NOT VALID 不阻塞 deploy
    op.execute(
        "ALTER TABLE knowledge_nodes "
        "ADD CONSTRAINT chk_depth_range CHECK (depth BETWEEN 1 AND 3) NOT VALID"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE knowledge_nodes DROP CONSTRAINT IF EXISTS chk_depth_range"
    )
