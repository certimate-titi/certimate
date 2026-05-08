"""resource_scaffolds add embedding vector(1024) — Sprint 7 P6 (T54).

加 1024 維 voyage embedding 到 resource_scaffolds，避免每次 /concept-center
語意搜尋都要重 embed（Sprint 6 T49 是即時 embed，~$0.0001/req）。

Backfill 策略（lazy）：
- 此 migration 只加欄位（nullable）
- 既有 scaffold 的 embedding 為 NULL
- 後續：
  1. 新解析 scaffold 在 _persist_parsed 自動寫 embedding（T54 後續）
  2. 既有 scaffold 由背景 task 漸進 backfill（Sprint 8 評估）
  3. /concept-center query 時：embedding IS NOT NULL 走語意搜尋；
     IS NULL 退回 ILIKE

Revision ID: 087
Revises: 086
"""

from alembic import op
import sqlalchemy as sa

revision = "087"
down_revision = "086"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE resource_scaffolds ADD COLUMN IF NOT EXISTS embedding vector(1024)"
    )
    # IVFFlat index 給 cosine similarity 查詢用
    # 注意：IVFFlat 須資料量 ≥ 1000 才有意義；目前 lazy backfill 暫不建 index
    # Sprint 8 P7 評估資料量足夠後再加：
    #   CREATE INDEX ON resource_scaffolds USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);


def downgrade() -> None:
    op.execute("ALTER TABLE resource_scaffolds DROP COLUMN IF EXISTS embedding")
