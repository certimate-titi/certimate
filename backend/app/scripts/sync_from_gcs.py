#!/usr/bin/env python3
"""
從 GCS Bucket 同步考古題 JSON 到本地目錄。

使用方式：
    # 作為 module 執行（需 DATABASE_URL 已設定）
    .venv/bin/python -m app.scripts.sync_from_gcs

    # 也可被 entrypoint.sh 或 API 呼叫
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

GCS_BUCKET = "certimate-titi-data"
GCS_PREFIX = "historical_questions/"
LOCAL_DIR = Path("/tmp/historical_questions")


def sync_from_gcs(
    bucket_name: str = GCS_BUCKET,
    prefix: str = GCS_PREFIX,
    local_dir: Path = LOCAL_DIR,
) -> dict:
    """下載 GCS bucket 中的考古題 JSON 到本地暫存目錄。

    Returns:
        dict with keys: downloaded, skipped, errors
    """
    try:
        from google.cloud import storage
    except ImportError:
        log.error("google-cloud-storage not installed. Run: pip install google-cloud-storage")
        return {"downloaded": 0, "skipped": 0, "errors": ["google-cloud-storage not installed"]}

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    downloaded = 0
    skipped = 0
    errors = []

    log.info(f"Syncing gs://{bucket_name}/{prefix} -> {local_dir}")

    try:
        blobs = list(bucket.list_blobs(prefix=prefix))
    except Exception as e:
        log.error(f"Failed to list blobs: {e}")
        return {"downloaded": 0, "skipped": 0, "errors": [str(e)]}

    if not blobs:
        log.warning("No blobs found in GCS bucket")
        return {"downloaded": 0, "skipped": 0, "errors": []}

    for blob in blobs:
        # Skip directory markers
        if blob.name.endswith("/"):
            continue

        # Only sync JSON files
        if not blob.name.endswith(".json"):
            continue

        # Build local path: strip the prefix, keep subdirectory structure
        relative = blob.name[len(prefix):]
        local_path = local_dir / relative

        # Skip if already exists and same size
        if local_path.exists() and local_path.stat().st_size == blob.size:
            skipped += 1
            continue

        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(local_path))
            downloaded += 1
        except Exception as e:
            log.error(f"Failed to download {blob.name}: {e}")
            errors.append(f"{blob.name}: {str(e)}")

    log.info(f"GCS sync complete: {downloaded} downloaded, {skipped} skipped, {len(errors)} errors")
    return {"downloaded": downloaded, "skipped": skipped, "errors": errors}


def sync_and_import(db_session=None) -> dict:
    """同步 GCS 並匯入到資料庫。

    Args:
        db_session: SQLAlchemy Session. If None, creates one from settings.

    Returns:
        dict with sync_result and import_result
    """
    from app.scripts.import_exam_questions import QuestionImporter

    # Step 1: Sync from GCS
    sync_result = sync_from_gcs()

    if sync_result["errors"] and sync_result["downloaded"] == 0:
        return {"sync_result": sync_result, "import_result": None}

    # Step 2: Import to DB
    own_session = False
    if db_session is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.core.config import get_settings

        engine = create_engine(get_settings().DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()
        own_session = True

    try:
        importer = QuestionImporter(db_session, dry_run=False)
        importer.import_directory(LOCAL_DIR)

        import_result = {
            "imported": importer.imported_count,
            "skipped": importer.skipped_count,
            "errors": importer.error_count,
        }
    finally:
        if own_session:
            db_session.close()

    return {"sync_result": sync_result, "import_result": import_result}


if __name__ == "__main__":
    result = sync_and_import()
    log.info(f"Result: {result}")
