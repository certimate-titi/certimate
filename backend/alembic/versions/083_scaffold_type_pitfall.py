"""Scaffold type add `pitfall` — Sprint 2 P1 (T11).

新增鷹架類別 pitfall（迷思警示）：
- 教學原理：Misconception Correction
- 與 takeaway 區別：takeaway 是「要記住的」，pitfall 是「容易誤解的」
- UI：紅色警示卡，預設展開（不需 retrieval-first）
- 來源：K-06 v5 從教材文本反向找出常見誤解

Postgres 限制：ALTER TYPE ADD VALUE 不能與其他 DDL 在同一 transaction 內，
但 alembic 預設每個 migration 一個 tx，所以這個 migration 只做 enum value 新增。

Revision ID: 083
Revises: 082
"""

from alembic import op

revision = "083"
down_revision = "082"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ADD VALUE 須 IF NOT EXISTS 因為已存在不會跳例外，重跑保留冪等
    op.execute(
        "ALTER TYPE resource_scaffold_type ADD VALUE IF NOT EXISTS 'pitfall'"
    )


def downgrade() -> None:
    # Postgres 不支援 ALTER TYPE DROP VALUE，僅能重建整個 enum。
    # 因 pitfall 為純加入、不影響舊資料；且任何 pitfall 鷹架先軟刪即可。
    # 這裡留 no-op，符合 P0 lazy-backfill 策略；若真要回退，須手動：
    #   1) DELETE FROM resource_scaffolds WHERE type = 'pitfall'
    #   2) CREATE TYPE resource_scaffold_type_new AS ENUM (...)
    #   3) ALTER COLUMN type TYPE resource_scaffold_type_new USING type::text::...
    pass
