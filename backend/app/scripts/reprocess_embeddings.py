#!/usr/bin/env python3
"""
重新處理考古題的向量嵌入和跳轉錨點。

因向量引擎更換或新增 anchor_id/highlight 欄位，需對現有 resource_chunks 重新處理：
1. 為所有缺少 anchor_id 的 chunk 生成錨點 ID
2. 重新生成 embedding 向量（使用最新的 Voyage 模型）
3. 清除 embedding 快取（確保使用新向量）

使用方式：
    # Dry-run（只顯示會處理的數量）
    .venv/bin/python -m app.scripts.reprocess_embeddings --dry-run

    # 僅更新 anchor_id（不重新生成 embedding）
    .venv/bin/python -m app.scripts.reprocess_embeddings --anchor-only

    # 完整重新處理（anchor_id + embedding）
    .venv/bin/python -m app.scripts.reprocess_embeddings

    # 指定 batch size
    .venv/bin/python -m app.scripts.reprocess_embeddings --batch-size 100
"""

import argparse
import logging
import sys
import time

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def update_anchors(db: Session, dry_run: bool = False) -> int:
    """為缺少 ``anchor_id`` 的 ``resource_chunks`` 補上錨點。

    若 chunk 有 ``source_page_start`` 則設為 ``page_{N}``，否則 fallback 為
    ``chunk_{chunk_index}``。

    Args:
        db: SQLAlchemy Session。
        dry_run: 若為 True 只計數不寫入。

    Returns:
        受影響（或在 dry-run 下將會受影響）的 chunk 數量。

    副作用：
        非 dry-run 會 ``UPDATE resource_chunks.anchor_id`` 並 ``commit``。
    """
    from app.models.resource_chunk import ResourceChunk

    chunks = (
        db.query(ResourceChunk)
        .filter(ResourceChunk.anchor_id.is_(None))
        .filter(ResourceChunk.is_deleted.is_(False))
        .all()
    )

    log.info(f"找到 {len(chunks)} 個缺少 anchor_id 的 chunk")

    if dry_run:
        return len(chunks)

    updated = 0
    for chunk in chunks:
        if chunk.source_page_start:
            chunk.anchor_id = f"page_{chunk.source_page_start}"
        else:
            chunk.anchor_id = f"chunk_{chunk.chunk_index}"
        updated += 1

    db.commit()
    log.info(f"✓ 已更新 {updated} 個 chunk 的 anchor_id")
    return updated


def reembed_chunks(db: Session, batch_size: int = 64, dry_run: bool = False) -> int:
    """以最新 Voyage 模型重新計算 ``resource_chunks.embedding``。

    Args:
        db: SQLAlchemy Session。
        batch_size: 每批送 Voyage 的 chunk 數，預設 64。
        dry_run: 若為 True 只回報總數不實際呼叫 embedding API。

    Returns:
        實際處理（或在 dry-run 下將會處理）的 chunk 數量。

    副作用：
        非 dry-run 會呼叫外部 Voyage API 並 ``UPDATE resource_chunks.embedding``，
        每批結束 ``commit``；連續 batch 失敗超過 5 次會中止。
    """
    from app.models.resource_chunk import ResourceChunk

    total = (
        db.query(func.count(ResourceChunk.id))
        .filter(ResourceChunk.is_deleted.is_(False))
        .scalar()
    )

    log.info(f"總計 {total} 個有效 chunk 需要重新嵌入")

    if dry_run:
        return total

    try:
        from app.services.embedding_service import EmbeddingService
        embed_svc = EmbeddingService()
    except Exception as e:
        log.error(f"無法初始化 EmbeddingService: {e}")
        log.error("請確認 VOYAGE_API_KEY 已設定")
        return 0

    processed = 0
    errors = 0
    start_time = time.time()

    # 分批處理
    offset = 0
    while offset < total:
        chunks = (
            db.query(ResourceChunk)
            .filter(ResourceChunk.is_deleted.is_(False))
            .order_by(ResourceChunk.created_at)
            .offset(offset)
            .limit(batch_size)
            .all()
        )

        if not chunks:
            break

        texts = [c.content for c in chunks]

        try:
            embeddings = embed_svc.embed_texts(texts, input_type="document")

            for chunk, emb in zip(chunks, embeddings):
                chunk.embedding = emb

            db.commit()
            processed += len(chunks)

            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total - processed) / rate if rate > 0 else 0

            log.info(
                f"  進度: {processed}/{total} ({processed * 100 // total}%) "
                f"| 速率: {rate:.1f} chunks/s "
                f"| ETA: {eta:.0f}s"
            )

        except Exception as e:
            log.error(f"  Batch embed 失敗 (offset={offset}): {e}")
            db.rollback()
            errors += 1
            if errors > 5:
                log.error("連續失敗過多，中止處理")
                break

        offset += batch_size

    elapsed = time.time() - start_time
    log.info(f"✓ 重新嵌入完成: {processed}/{total} chunks, {elapsed:.1f}s, {errors} errors")
    return processed


def clear_embedding_cache():
    """清空 ``EmbeddingService`` 的 in-memory LRU 快取。

    避免重新 embed 後因 process 內快取仍指向舊向量而拿到過期結果。失敗時
    僅輸出警告 log，不 raise。

    副作用：
        重置 ``_embedding_cache`` 的 ``_store`` / ``_hit_count`` /
        ``_miss_count``。
    """
    try:
        from app.services.embedding_service import _embedding_cache
        stats = _embedding_cache.stats
        log.info(f"清除前快取統計: {stats}")
        _embedding_cache._store.clear()
        _embedding_cache._hit_count = 0
        _embedding_cache._miss_count = 0
        log.info("✓ Embedding 快取已清除")
    except Exception as e:
        log.warning(f"清除快取失敗（可忽略）: {e}")


def main():
    """CLI 進入點：依參數選擇執行 anchor 補值、embedding 重算與快取清除。

    可組合 ``--anchor-only`` / ``--embed-only`` / ``--clear-cache`` /
    ``--dry-run`` / ``--batch-size`` 等旗標決定執行步驟。

    副作用：
        非 dry-run 會大量 ``UPDATE resource_chunks``、呼叫 Voyage API 並清
        除 in-process embedding 快取。
    """
    parser = argparse.ArgumentParser(
        description="重新處理考古題的向量嵌入和跳轉錨點"
    )
    parser.add_argument("--dry-run", action="store_true", help="模擬執行，不寫入資料庫")
    parser.add_argument("--anchor-only", action="store_true", help="僅更新 anchor_id（不重新生成 embedding）")
    parser.add_argument("--embed-only", action="store_true", help="僅重新生成 embedding（不更新 anchor_id）")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding batch size（預設 64）")
    parser.add_argument("--clear-cache", action="store_true", help="清除 embedding 快取")

    args = parser.parse_args()

    log.info("=" * 60)
    log.info("CertiMate 考古題重新處理")
    log.info("=" * 60)
    log.info(f"模式: {'dry-run' if args.dry_run else 'LIVE'}")
    log.info(f"資料庫: {settings.DATABASE_URL[:50]}...")

    engine = create_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Step 1: 更新 anchor_id
        if not args.embed_only:
            log.info("")
            log.info("━" * 40)
            log.info("Step 1: 更新 anchor_id + highlight 欄位")
            log.info("━" * 40)
            anchor_count = update_anchors(db, dry_run=args.dry_run)

        # Step 2: 重新生成 embedding
        if not args.anchor_only:
            log.info("")
            log.info("━" * 40)
            log.info("Step 2: 重新生成 embedding 向量")
            log.info("━" * 40)
            embed_count = reembed_chunks(db, batch_size=args.batch_size, dry_run=args.dry_run)

        # Step 3: 清除快取
        if args.clear_cache or (not args.dry_run and not args.anchor_only):
            log.info("")
            log.info("━" * 40)
            log.info("Step 3: 清除 embedding 快取")
            log.info("━" * 40)
            clear_embedding_cache()

        # 摘要
        log.info("")
        log.info("=" * 60)
        log.info("處理摘要")
        log.info("=" * 60)
        if not args.embed_only:
            log.info(f"  Anchor ID 更新: {anchor_count}")
        if not args.anchor_only:
            log.info(f"  Embedding 重新生成: {embed_count}")
        log.info(f"  模式: {'🔍 dry-run（未寫入）' if args.dry_run else '✅ 已提交到資料庫'}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
