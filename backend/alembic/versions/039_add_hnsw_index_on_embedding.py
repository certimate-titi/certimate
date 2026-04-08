"""Upgrade vector index from IVFFlat to HNSW on resource_chunks.embedding.

Revision ID: 039
Revises: 038
Create Date: 2026-04-08

Phase 1 向量索引優化：
- 移除舊的 IVFFlat 索引（適合靜態資料）
- 建立 HNSW 索引（適合動態插入，支援 Pre-filtering by tenant_id）
- 建立 (tenant_id, embedding) 複合概念索引
  （HNSW 本身不支援複合欄位，但搭配 tenant_id IS NOT NULL 的部分索引）
- HNSW 參數：m=16, ef_construction=64（平衡效能 vs 準確率）
"""
from alembic import op
import sqlalchemy as sa

revision = "039"
down_revision = "038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector 擴充（若尚未啟用）
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    # 移除舊的 IVFFlat 索引（若存在）
    op.execute(sa.text(
        "DROP INDEX IF EXISTS resource_chunks_embedding_idx"
    ))
    op.execute(sa.text(
        "DROP INDEX IF EXISTS ix_resource_chunks_embedding"
    ))

    # 建立 HNSW 索引（cosine 距離，適合文本語意相似度）
    # m=16: 每個節點最多 16 條連結（越大召回率越高，記憶體越多）
    # ef_construction=64: 建構時的搜尋寬度（越大索引品質越高，建構越慢）
    op.execute(sa.text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_resource_chunks_embedding_hnsw
        ON resource_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """))

    # 建立 tenant_id 複合過濾索引（先過濾租戶，再做向量搜尋 Pre-filtering）
    # 注意：HNSW 不支援複合欄位，但可用 WHERE 子句建立 Partial Index
    op.execute(sa.text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_resource_chunks_tenant_embedding
        ON resource_chunks (tenant_id)
        WHERE tenant_id IS NOT NULL
    """))

    # 設定 HNSW 查詢參數的說明（runtime 設定，不在 migration 中強制）
    # 使用時應設定 SET hnsw.ef_search = 100 以平衡速度與精度
    op.execute(sa.text("""
        COMMENT ON INDEX ix_resource_chunks_embedding_hnsw
        IS 'HNSW cosine index for semantic search. Set hnsw.ef_search=100 at query time.'
    """))


def downgrade() -> None:
    op.execute(sa.text(
        "DROP INDEX CONCURRENTLY IF EXISTS ix_resource_chunks_tenant_embedding"
    ))
    op.execute(sa.text(
        "DROP INDEX CONCURRENTLY IF EXISTS ix_resource_chunks_embedding_hnsw"
    ))
    # 恢復 IVFFlat（需要資料存在才能建立 lists 參數，此處用保守值）
    op.execute(sa.text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS resource_chunks_embedding_idx
        ON resource_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """))
