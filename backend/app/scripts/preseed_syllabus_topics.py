"""Seed syllabus_topics from Claude Code local-LLM output (Feature 34 §3 Strategy E).

Usage:
    DATABASE_URL=... .venv/bin/python -m app.scripts.preseed_syllabus_topics \
        --input /tmp/preseed_output_infosec.json [--dry-run] [--replace]

Input JSON schema (produced by preseed-mindmaps skill Phase 2):
{
    "subject_id": "uuid",
    "subject_name": "...",
    "source": "claude-code-local-llm",
    "tree": [
        {
            "name": "章名",
            "description": "章說明（選填）",
            "weight": 1.5,
            "sections": [
                {"name": "節名", "weight": 1.0}
            ]
        }
    ]
}

Writes:
- syllabus_topics(subject_id=sid, parent_id=None, name=chapter, depth=0)
- syllabus_topics(subject_id=sid, parent_id=chapter, name=section, depth=1)

--replace: delete existing subject_id rows before insert (idempotent re-seed)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def seed(
    db: Session,
    payload: dict,
    *,
    dry_run: bool = False,
    replace: bool = False,
) -> dict:
    """將 preseed-mindmaps Phase 2 產出的章節樹寫入 ``syllabus_topics``。

    Args:
        db: SQLAlchemy Session。
        payload: Phase 2 JSON dict，須包含 ``subject_id`` 與 ``tree``（章 →
            節 兩層結構）。
        dry_run: 是否模擬執行（True 不寫入 DB）。
        replace: 是否在插入前 ``DELETE FROM syllabus_topics WHERE subject_id
            = :sid`` 以實現冪等重新 seed。

    Returns:
        包含 ``subject_id`` / ``subject_name`` / ``chapters`` / ``sections``
        / ``dry_run`` 統計的 dict；找不到 subject 或 ``tree`` 為空時改回傳
        ``{"error": ...}``。

    副作用：
        非 dry-run 時會 INSERT 章 / 節兩層 ``syllabus_topics``，並在 replace
        模式下先刪除既有列；最後執行 ``db.commit()``。
    """
    subject_id = payload["subject_id"]
    subject_name = payload.get("subject_name", "?")
    tree = payload.get("tree", [])

    if not tree:
        return {"error": "tree is empty"}

    # Verify subject exists
    row = db.execute(
        text("SELECT name FROM subjects WHERE id = :sid"),
        {"sid": subject_id},
    ).first()
    if not row:
        return {"error": f"subject {subject_id} not found"}

    log.info(f"[seed] target subject: {row[0]} ({subject_id})")

    # Replace mode: delete existing
    if replace:
        result = db.execute(
            text("DELETE FROM syllabus_topics WHERE subject_id = :sid"),
            {"sid": subject_id},
        )
        log.info(f"[seed] cleared {result.rowcount} existing topics")

    chapter_count = 0
    section_count = 0

    for chapter in tree:
        chapter_id = uuid.uuid4()
        chapter_count += 1
        if not dry_run:
            db.execute(
                text(
                    """
                    INSERT INTO syllabus_topics
                      (id, subject_id, parent_id, name, depth, weight, is_active)
                    VALUES
                      (:id, :sid, NULL, :name, 0, :w, true)
                    """
                ),
                {
                    "id": chapter_id,
                    "sid": subject_id,
                    "name": chapter["name"],
                    "w": float(chapter.get("weight", 1.0)),
                },
            )
        log.info(
            f"  [ch] {chapter['name']} (w={chapter.get('weight', 1.0)})"
        )
        for section in chapter.get("sections", []):
            section_count += 1
            if not dry_run:
                db.execute(
                    text(
                        """
                        INSERT INTO syllabus_topics
                          (id, subject_id, parent_id, name, depth, weight, is_active)
                        VALUES
                          (:id, :sid, :pid, :name, 1, :w, true)
                        """
                    ),
                    {
                        "id": uuid.uuid4(),
                        "sid": subject_id,
                        "pid": chapter_id,
                        "name": section["name"],
                        "w": float(section.get("weight", 1.0)),
                    },
                )
            log.info(f"    [sec] {section['name']}")

    if not dry_run:
        db.commit()

    result = {
        "subject_id": subject_id,
        "subject_name": subject_name,
        "chapters": chapter_count,
        "sections": section_count,
        "dry_run": dry_run,
    }
    log.info(
        f"[seed] DONE — chapters={chapter_count} sections={section_count}"
        f"{' (DRY RUN)' if dry_run else ''}"
    )
    return result


def main():
    """CLI 進入點：載入 ``--input`` JSON 並呼叫 :func:`seed`。

    要求環境變數 ``DATABASE_URL`` 已設定；執行結果 JSON 印到 stdout，遇錯
    以非零狀態碼結束。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Phase 2 JSON path")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--replace", action="store_true",
        help="Delete existing rows for this subject before insert",
    )
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        log.error("DATABASE_URL not set")
        sys.exit(1)

    with open(args.input) as f:
        payload = json.load(f)

    engine = create_engine(db_url)
    with Session(engine) as db:
        result = seed(db, payload, dry_run=args.dry_run, replace=args.replace)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("error"):
            sys.exit(1)


if __name__ == "__main__":
    main()
