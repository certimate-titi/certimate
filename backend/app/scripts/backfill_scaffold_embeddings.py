#!/usr/bin/env python3
"""Backfill voyage embedding for resource_scaffolds where embedding IS NULL.

Sprint 8 T57：T54 是 lazy 寫入 — 新 parse 自動寫，既有舊 scaffolds 為 NULL。
此腳本批次掃描補齊，配合 /concept-center 完全走 DB 內 cosine similarity。

用法：
    # Dry-run（只顯示需補的數量）
    .venv/bin/python -m app.scripts.backfill_scaffold_embeddings --dry-run

    # 實際 backfill（預設 batch=64，符合 voyage 限制）
    .venv/bin/python -m app.scripts.backfill_scaffold_embeddings

    # 限制處理筆數（避免一次燒太多 voyage 配額）
    .venv/bin/python -m app.scripts.backfill_scaffold_embeddings --limit 500

設計：
- 失敗不阻斷整輪：單批 voyage 失敗只 log + 跳過，下次再跑
- 每批 commit：中斷後可從上次斷點續跑（embedding IS NULL 自然過濾）
- 不重 embed 已有 vector 的 row（IS NULL 條件）
"""

import argparse
import logging
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def count_null_embeddings(db: Session) -> int:
    return db.execute(
        text("SELECT COUNT(*) FROM resource_scaffolds WHERE embedding IS NULL")
    ).scalar_one()


def fetch_batch(db: Session, batch_size: int) -> list[tuple]:
    return db.execute(
        text(
            """
            SELECT id, chapter_heading, content
            FROM resource_scaffolds
            WHERE embedding IS NULL
            ORDER BY created_at
            LIMIT :n
            """
        ),
        {"n": batch_size},
    ).fetchall()


def write_batch(db: Session, ids: list, vecs: list[list[float]]) -> int:
    """逐 row UPDATE — pgvector 沒有 bulk update 語法，但每批 64 筆夠快。"""
    written = 0
    for sid, vec in zip(ids, vecs):
        db.execute(
            text(
                "UPDATE resource_scaffolds SET embedding = :v WHERE id = :id"
            ),
            {"v": str(vec), "id": str(sid)},
        )
        written += 1
    return written


def run(batch_size: int, limit: int | None, dry_run: bool) -> None:
    engine = create_engine(settings.DATABASE_URL)
    Sm = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with Sm() as db:
        total_null = count_null_embeddings(db)
        log.info("scaffolds with NULL embedding: %d", total_null)
        if dry_run:
            log.info("[dry-run] no changes; would process %d rows",
                     min(total_null, limit or total_null))
            return
        if total_null == 0:
            log.info("nothing to backfill, exit")
            return

    from app.services.embedding_service import EmbeddingService

    emb = EmbeddingService()
    processed = 0
    errors = 0
    target = limit or total_null
    started = time.monotonic()

    while processed < target:
        with Sm() as db:
            rows = fetch_batch(db, min(batch_size, target - processed))
            if not rows:
                break

            ids = [r[0] for r in rows]
            texts = [
                ((r[1] or "") + " " + (r[2] or "")).strip()[:1000] for r in rows
            ]

            try:
                vecs = emb.embed_texts(texts, input_type="document")
            except Exception as e:
                errors += 1
                log.warning("[backfill] batch failed (skip): %s", e)
                processed += len(rows)
                continue

            written = write_batch(db, ids, vecs)
            db.commit()
            processed += written
            log.info(
                "[backfill] +%d rows (total=%d/%d, errors=%d, elapsed=%.1fs)",
                written, processed, target, errors,
                time.monotonic() - started,
            )

    log.info(
        "done: processed=%d errors=%d remaining_null=%d",
        processed, errors, count_null_embeddings(Sm()),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=64,
                        help="voyage embed 每批筆數（max 128）")
    parser.add_argument("--limit", type=int, default=None,
                        help="本次最多處理筆數（避免燒爆配額）")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.batch_size, args.limit, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
