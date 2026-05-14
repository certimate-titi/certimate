"""Backfill hashtag tags for legacy content.

PR #96/#99 added hashtag parser but only triggered on create/update.
Existing notes / annotations / scaffolds with `#tag` in content never got
parsed → tag tables empty → aggregate endpoint returns nothing.

This script is IDEMPOTENT: `INSERT ... ON CONFLICT DO NOTHING` ensures
repeated runs do not create duplicate rows.

Usage (CLI):
    .venv/bin/python -m app.scripts.backfill_hashtag_tags

Or triggered via POST /api/v1/admin/backfill-tags (SUPER_ADMIN only).
"""

import logging
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.utils.markdown_hashtags import extract_hashtags

logger = logging.getLogger(__name__)


# ── helpers ────────────────────────────────────────────────────────────────


def _upsert_user_note_tags(db: Session) -> int:
    """掃 user_notes，對每筆 content 解析 hashtag，INSERT ON CONFLICT DO NOTHING 至 user_note_tags。

    Returns:
        total rows inserted
    """
    rows = db.execute(
        text("SELECT id, content FROM user_notes WHERE content IS NOT NULL")
    ).fetchall()

    inserted = 0
    for row in rows:
        note_id = row[0]
        content = row[1]
        tag_pairs = extract_hashtags(content)
        for normalized, display in tag_pairs:
            result = db.execute(
                text(
                    """
                    INSERT INTO user_note_tags (note_id, tag_normalized, tag_display)
                    VALUES (:note_id, :tag_normalized, :tag_display)
                    ON CONFLICT (note_id, tag_normalized) DO NOTHING
                    """
                ),
                {
                    "note_id": str(note_id),
                    "tag_normalized": normalized[:64],
                    "tag_display": display[:80],
                },
            )
            inserted += result.rowcount
    db.commit()
    return inserted


def _upsert_chat_annotation_tags(db: Session) -> int:
    """掃 chat_message_annotations，對每筆 user_annotation 解析 hashtag，INSERT ON CONFLICT DO NOTHING 至 chat_annotation_tags。

    Returns:
        total rows inserted
    """
    rows = db.execute(
        text(
            "SELECT id, user_annotation FROM chat_message_annotations WHERE user_annotation IS NOT NULL"
        )
    ).fetchall()

    inserted = 0
    for row in rows:
        annotation_id = row[0]
        user_annotation = row[1]
        tag_pairs = extract_hashtags(user_annotation)
        for normalized, display in tag_pairs:
            result = db.execute(
                text(
                    """
                    INSERT INTO chat_annotation_tags (annotation_id, tag_normalized, tag_display)
                    VALUES (:annotation_id, :tag_normalized, :tag_display)
                    ON CONFLICT (annotation_id, tag_normalized) DO NOTHING
                    """
                ),
                {
                    "annotation_id": str(annotation_id),
                    "tag_normalized": normalized[:64],
                    "tag_display": display[:80],
                },
            )
            inserted += result.rowcount
    db.commit()
    return inserted


def _upsert_scaffold_tags(db: Session) -> int:
    """掃 resource_scaffolds（含 user_response），JOIN resources.user_id，
    跳過 resource_id IS NULL（admin/seed orphan），INSERT ON CONFLICT DO NOTHING 至 scaffold_tags。

    scaffold_tags PK = (scaffold_id, user_id, tag_normalized)，user_id 從 resources.user_id 取得。

    Returns:
        total rows inserted
    """
    rows = db.execute(
        text(
            """
            SELECT rs.id, rs.user_response, r.user_id
            FROM resource_scaffolds rs
            JOIN resources r ON rs.resource_id = r.id
            WHERE rs.user_response IS NOT NULL
              AND rs.resource_id IS NOT NULL
              AND r.user_id IS NOT NULL
            """
        )
    ).fetchall()

    inserted = 0
    for row in rows:
        scaffold_id = row[0]
        user_response = row[1]
        user_id = row[2]
        tag_pairs = extract_hashtags(user_response)
        for normalized, display in tag_pairs:
            result = db.execute(
                text(
                    """
                    INSERT INTO scaffold_tags (scaffold_id, user_id, tag_normalized, tag_display)
                    VALUES (:scaffold_id, :user_id, :tag_normalized, :tag_display)
                    ON CONFLICT (scaffold_id, user_id, tag_normalized) DO NOTHING
                    """
                ),
                {
                    "scaffold_id": str(scaffold_id),
                    "user_id": str(user_id),
                    "tag_normalized": normalized[:64],
                    "tag_display": display[:80],
                },
            )
            inserted += result.rowcount
    db.commit()
    return inserted


# ── main run ───────────────────────────────────────────────────────────────


def run(db: Session | None = None) -> dict[str, Any]:
    """執行所有三類筆記的 hashtag backfill。

    Args:
        db: 可選外部傳入 Session（用於 admin endpoint）；None 時自建 engine。

    Returns:
        {
            user_notes_processed: int,
            annotations_processed: int,
            scaffolds_processed: int,
            total_tags_inserted: int,
        }
    """
    own_session = db is None
    if own_session:
        from app.core.config import get_settings
        _settings = get_settings()
        # Strip async driver prefixes — create_engine needs sync driver
        db_url = _settings.DATABASE_URL.replace("+asyncpg", "").replace("+psycopg", "")
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
        db = SessionLocal()

    try:
        logger.info("[backfill_hashtag_tags] Starting user_notes ...")
        notes_inserted = _upsert_user_note_tags(db)

        logger.info("[backfill_hashtag_tags] Starting chat_annotation_tags ...")
        annotations_inserted = _upsert_chat_annotation_tags(db)

        logger.info("[backfill_hashtag_tags] Starting scaffold_tags ...")
        scaffolds_inserted = _upsert_scaffold_tags(db)

        total = notes_inserted + annotations_inserted + scaffolds_inserted

        result: dict[str, Any] = {
            "user_notes_processed": notes_inserted,
            "annotations_processed": annotations_inserted,
            "scaffolds_processed": scaffolds_inserted,
            "total_tags_inserted": total,
        }
        logger.info("[backfill_hashtag_tags] Done: %s", result)
        return result
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    report = run()
    print(report)
