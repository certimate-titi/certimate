#!/usr/bin/env python3
"""
Feature 26 — 考綱逆向工程：統一知識樹萃取（thin wrapper）。

用法：
    cd backend
    .venv/bin/python scripts/reverse_engineer_syllabus.py              # 萃取缺少節點的科目
    .venv/bin/python scripts/reverse_engineer_syllabus.py --all        # 重新萃取所有科目
    .venv/bin/python scripts/reverse_engineer_syllabus.py --subject-id <uuid>  # 萃取指定科目

底層呼叫 UnifiedKnowledgeExtractionService，合併考古題 + 用戶資源 chunks 統一萃取。
"""

import sys
import time
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.services.unified_knowledge_extraction_service import UnifiedKnowledgeExtractionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

MIN_NODE_THRESHOLD = 5  # 少於此數量的知識節點視為需要萃取


def get_subjects(db, *, all_subjects: bool = False, subject_id: str | None = None) -> list[dict]:
    """取得需要萃取的科目清單。"""
    if subject_id:
        row = db.execute(text('''
            SELECT s.id, s.name, s.available_questions,
                   (SELECT COUNT(*) FROM knowledge_nodes kn WHERE kn.subject_id = s.id) as node_count
            FROM subjects s WHERE s.id = :sid
        '''), {'sid': subject_id}).fetchone()
        return [{"id": str(row[0]), "name": row[1], "question_count": row[2], "node_count": row[3]}] if row else []

    rows = db.execute(text('''
        SELECT s.id, s.name, s.available_questions,
               (SELECT COUNT(*) FROM knowledge_nodes kn WHERE kn.subject_id = s.id) as node_count
        FROM subjects s
        WHERE s.available_questions > 0
        ORDER BY s.available_questions DESC
    ''')).fetchall()

    return [
        {"id": str(r[0]), "name": r[1], "question_count": r[2], "node_count": r[3]}
        for r in rows
        if all_subjects or r[3] < MIN_NODE_THRESHOLD
    ]


def main():
    parser = argparse.ArgumentParser(description="統一知識樹萃取")
    parser.add_argument("--all", action="store_true", help="重新萃取所有有考古題的科目")
    parser.add_argument("--subject-id", type=str, help="指定科目 UUID")
    args = parser.parse_args()

    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)

    db = Session()
    subjects = get_subjects(db, all_subjects=args.all, subject_id=args.subject_id)
    db.close()

    log.info(f"需要萃取的科目: {len(subjects)}")

    success, fail = 0, 0
    for subj in subjects:
        log.info(f"\n{'='*60}")
        log.info(f"科目: {subj['name']} ({subj['question_count']} 題, 現有 {subj['node_count']} 節點)")
        log.info(f"{'='*60}")

        db = Session()
        try:
            svc = UnifiedKnowledgeExtractionService(db)
            result = svc.extract(subj["id"])

            if result.get("ok"):
                log.info(f"  ✅ 完成: {result['nodes_created']} 節點, mastery遷移={result['mastery_migrated']}")
                success += 1
            else:
                log.error(f"  ❌ 失敗: {result.get('message')}")
                fail += 1
        except Exception as e:
            log.error(f"  ❌ 異常: {e}", exc_info=True)
            fail += 1
        finally:
            db.close()

        time.sleep(2)  # Gemini rate limit

    log.info(f"\n{'='*60}")
    log.info(f"全部完成: {success} 成功, {fail} 失敗")


if __name__ == "__main__":
    main()
