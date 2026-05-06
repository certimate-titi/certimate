"""Purge soft-deleted subjects and resources — CLI 工具.

此腳本掃描 deleted_at IS NOT NULL 的 subjects 與 resources（如存在此欄位），
執行硬刪除並列出連帶清除的筆數。

WARNING: --execute 為不可逆操作，建議先以 --dry-run 確認影響範圍。

使用方式：
    # 模擬執行（列出將被刪除的項目，不實際刪除）
    python -m app.scripts.purge_soft_deleted --dry-run

    # 正式執行（每 100 筆 commit）
    python -m app.scripts.purge_soft_deleted --execute

    # 只清 resources
    python -m app.scripts.purge_soft_deleted --execute --only resources

    # 只清 subjects
    python -m app.scripts.purge_soft_deleted --execute --only subjects

完成後建議手動執行：
    psql $DATABASE_URL -c "VACUUM ANALYZE subjects, resources;"

環境變數：
    DATABASE_URL — PostgreSQL 連線字串（必須）
"""

import argparse
import logging
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 100


# ---------------------------------------------------------------------------
# DB 連線
# ---------------------------------------------------------------------------

def _create_session():
    """建立 SQLAlchemy sync session（腳本專用）。"""
    from app.core.config import get_settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    settings = get_settings()
    db_url = settings.DATABASE_URL
    if not db_url:
        logger.error("DATABASE_URL 未設定，請設定環境變數後重試。")
        sys.exit(1)

    # psycopg3 driver URL → psycopg2 相容 fallback
    if "postgresql+psycopg://" in db_url and "psycopg2" not in db_url:
        db_url = db_url.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)

    engine = create_engine(db_url, pool_pre_ping=True, echo=False)
    Session = sessionmaker(bind=engine, autoflush=False)
    return Session(), engine


# ---------------------------------------------------------------------------
# 輔助：計算 cascade 影響筆數（複用 subject_service 邏輯）
# ---------------------------------------------------------------------------

def _cascade_counts_subject(db, subject_id: str) -> dict[str, int]:
    from sqlalchemy import text as _t
    sid = str(subject_id)
    tables = [
        "resources", "exams", "knowledge_nodes",
        "learning_journeys", "syllabus_topics",
        "subject_default_resources",
    ]
    counts: dict[str, int] = {}
    for tbl in tables:
        try:
            row = db.execute(
                _t(f"SELECT COUNT(*) FROM {tbl} WHERE subject_id = :s"), {"s": sid}
            ).fetchone()
            counts[tbl] = int(row[0]) if row else 0
        except Exception:
            counts[tbl] = -1
    return counts


def _cascade_counts_resource(db, resource_id: str) -> dict[str, int]:
    from sqlalchemy import text as _t
    rid = str(resource_id)
    tables = [
        "resource_chunks", "resource_parse_jobs",
        "resource_scaffolds", "question_candidates", "knowledge_nodes",
    ]
    counts: dict[str, int] = {}
    for tbl in tables:
        try:
            row = db.execute(
                _t(f"SELECT COUNT(*) FROM {tbl} WHERE resource_id = :r"), {"r": rid}
            ).fetchone()
            counts[tbl] = int(row[0]) if row else 0
        except Exception:
            counts[tbl] = -1
    return counts


# ---------------------------------------------------------------------------
# 掃描函式
# ---------------------------------------------------------------------------

def _find_soft_deleted_subjects(db) -> list[Any]:
    """找 subjects.deleted_at IS NOT NULL（若欄位不存在則回傳空清單）。"""
    from sqlalchemy import text as _t
    try:
        rows = db.execute(
            _t("SELECT id, name FROM subjects WHERE deleted_at IS NOT NULL ORDER BY deleted_at")
        ).fetchall()
        return list(rows)
    except Exception as exc:
        logger.info("subjects 無 deleted_at 欄位（或查詢失敗）：%s", exc)
        return []


def _find_soft_deleted_resources(db) -> list[Any]:
    """找 resources.deleted_at IS NOT NULL（若欄位不存在則回傳空清單）。"""
    from sqlalchemy import text as _t
    try:
        rows = db.execute(
            _t("SELECT id, name FROM resources WHERE deleted_at IS NOT NULL ORDER BY deleted_at")
        ).fetchall()
        return list(rows)
    except Exception as exc:
        logger.info("resources 無 deleted_at 欄位（或查詢失敗）：%s", exc)
        return []


# ---------------------------------------------------------------------------
# 執行函式
# ---------------------------------------------------------------------------

def _purge_subjects(db, subjects: list[Any], dry_run: bool) -> int:
    """硬刪 subjects，回傳刪除筆數。"""
    from sqlalchemy import text as _t
    from app.models.exam import Exam
    from app.models.resource import Resource
    from app.models.subject import Subject

    deleted = 0
    for i, row in enumerate(subjects):
        sid = str(row[0])
        name = row[1] or "(no name)"
        counts = _cascade_counts_subject(db, sid)

        logger.info(
            "[Subject] %s — %s | cascade: %s",
            sid, name, counts
        )

        if dry_run:
            continue

        try:
            # 清 orphan questions
            db.execute(_t(
                "DELETE FROM questions WHERE exam_id IS NULL AND historical_exam_id IS NULL"
            ))

            # 手動刪 exams
            import uuid as _uuid
            sid_uuid = _uuid.UUID(sid)
            exams = db.query(Exam).filter(Exam.subject_id == sid_uuid).all()
            for e in exams:
                db.delete(e)
            db.flush()

            # 刪 resources
            res_list = db.query(Resource).filter(Resource.subject_id == sid_uuid).all()
            for r in res_list:
                db.delete(r)
            db.flush()

            # 刪 subject
            subj = db.query(Subject).filter(Subject.id == sid_uuid).first()
            if subj:
                db.delete(subj)

            deleted += 1

            if deleted % BATCH_SIZE == 0:
                db.commit()
                logger.info("Committed %d subjects so far", deleted)

        except Exception as exc:
            db.rollback()
            logger.error("刪除 subject %s 失敗，跳過：%s", sid, exc)

    if not dry_run and deleted % BATCH_SIZE != 0:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("Final commit failed: %s", exc)

    return deleted


def _purge_resources(db, resources: list[Any], dry_run: bool) -> int:
    """硬刪 resources，回傳刪除筆數。"""
    from sqlalchemy import text as _t
    from app.models.resource import Resource

    deleted = 0
    for i, row in enumerate(resources):
        rid = str(row[0])
        name = row[1] or "(no name)"
        counts = _cascade_counts_resource(db, rid)

        logger.info(
            "[Resource] %s — %s | cascade: %s",
            rid, name, counts
        )

        if dry_run:
            continue

        try:
            db.execute(_t(
                "DELETE FROM questions WHERE exam_id IS NULL AND historical_exam_id IS NULL"
            ))
            import uuid as _uuid
            res = db.query(Resource).filter(Resource.id == _uuid.UUID(rid)).first()
            if res:
                gcs_path = res.gcs_path
                db.delete(res)
                deleted += 1

                # 非阻斷性清 GCS
                if gcs_path:
                    try:
                        from app.services.storage_service import get_storage_service
                        get_storage_service().delete_file(gcs_path)
                    except Exception as exc:
                        logger.warning("GCS delete skipped for %s: %s", gcs_path, exc)

            if deleted % BATCH_SIZE == 0:
                db.commit()
                logger.info("Committed %d resources so far", deleted)

        except Exception as exc:
            db.rollback()
            logger.error("刪除 resource %s 失敗，跳過：%s", rid, exc)

    if not dry_run and deleted % BATCH_SIZE != 0:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("Final commit failed: %s", exc)

    return deleted


# ---------------------------------------------------------------------------
# 主程式
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="清除 soft-deleted subjects / resources（硬刪除）"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run", action="store_true",
        help="模擬執行：列出將被刪除的項目與連帶筆數，不做任何修改（預設安全模式）",
    )
    mode.add_argument(
        "--execute", action="store_true",
        help="正式執行：不可逆操作，每 100 筆 commit",
    )
    parser.add_argument(
        "--only", choices=["subjects", "resources"],
        default=None,
        help="只清指定資料表（省略則兩者都清）",
    )
    args = parser.parse_args()

    dry_run: bool = args.dry_run
    mode_label = "DRY-RUN" if dry_run else "EXECUTE"
    logger.info("=== purge_soft_deleted [%s] 開始 ===", mode_label)

    db, engine = _create_session()

    try:
        total_subjects = 0
        total_resources = 0

        # 掃描 subjects
        if args.only in (None, "subjects"):
            subjects = _find_soft_deleted_subjects(db)
            logger.info("找到 %d 筆 soft-deleted subjects", len(subjects))
            if subjects:
                total_subjects = _purge_subjects(db, subjects, dry_run)

        # 掃描 resources
        if args.only in (None, "resources"):
            resources = _find_soft_deleted_resources(db)
            logger.info("找到 %d 筆 soft-deleted resources", len(resources))
            if resources:
                total_resources = _purge_resources(db, resources, dry_run)

        if dry_run:
            logger.info(
                "=== DRY-RUN 完成：subjects=%d, resources=%d（未實際刪除）===",
                len(subjects) if args.only in (None, "subjects") else 0,
                len(resources) if args.only in (None, "resources") else 0,
            )
        else:
            logger.info(
                "=== EXECUTE 完成：已刪除 subjects=%d, resources=%d ===",
                total_subjects, total_resources,
            )
            logger.info(
                "建議執行：psql $DATABASE_URL -c \"VACUUM ANALYZE subjects, resources;\""
            )

    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    main()
