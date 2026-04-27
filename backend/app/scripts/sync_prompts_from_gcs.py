"""Sync prompt templates from GCS and seed to DB.

Usage:
    python -m app.scripts.sync_prompts_from_gcs

Flow:
    1. Download .md files from gs://certimate-titi-data/prompt_templates/ → /tmp/prompt_templates/
    2. Set PROMPT_TEMPLATES_DIR=/tmp/prompt_templates
    3. Run seed_prompts (version-based upsert — idempotent)

Called by entrypoint.sh on every Cloud Run cold start.
Non-fatal — if GCS has no prompt templates, logs warning and returns.
"""

import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

GCS_BUCKET = "certimate-titi-data"
GCS_PREFIX = "prompt_templates/"
LOCAL_DIR = Path("/tmp/prompt_templates")


def sync_prompts_from_gcs() -> dict:
    """從 GCS 下載 Prompt 模板 ``.md`` 檔到本地 ``/tmp/prompt_templates/``。

    僅下載大小或路徑與本地不一致的檔案，缺少 ``google-cloud-storage`` 套件
    或 GCS 列舉失敗時回傳 ``{"downloaded": 0, "error": ...}`` 而不 raise。

    Returns:
        ``{"downloaded": int}`` 或包含 ``error`` 欄位的失敗結果 dict。

    副作用：
        在 ``LOCAL_DIR`` 下建立 / 覆寫 ``.md`` 檔。
    """
    try:
        from google.cloud import storage
    except ImportError:
        return {"downloaded": 0, "error": "google-cloud-storage not installed"}

    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)

    downloaded = 0
    try:
        blobs = list(bucket.list_blobs(prefix=GCS_PREFIX))
    except Exception as e:
        log.warning(f"GCS prompt sync failed: {e}")
        return {"downloaded": 0, "error": str(e)}

    for blob in blobs:
        if blob.name.endswith("/") or not blob.name.endswith(".md"):
            continue
        relative = blob.name[len(GCS_PREFIX):]
        local_path = LOCAL_DIR / relative
        if local_path.exists() and local_path.stat().st_size == blob.size:
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
        downloaded += 1

    return {"downloaded": downloaded}


def sync_and_seed_prompts() -> dict:
    """先從 GCS 下載 Prompt 模板，再呼叫 :func:`seed_prompts.seed_all` 同步到 DB。

    被 ``entrypoint.sh`` 在 Cloud Run cold start 時呼叫，是 non-fatal —
    若 GCS 沒有模板或本地無 ``.md`` 檔則跳過 seed 並回 ``"skipped"``。

    Returns:
        ``{"sync": <sync_result>, "seed": <seed_result | message>}``。

    副作用：
        - 寫檔到 ``/tmp/prompt_templates/``。
        - 設環境變數 ``PROMPT_TEMPLATES_DIR``。
        - 觸發 :func:`seed_prompts.seed_all`，間接寫入 DB。
    """
    sync_result = sync_prompts_from_gcs()

    # Check if any .md files exist locally (either from GCS or pre-existing)
    md_files = list(LOCAL_DIR.rglob("*.md")) if LOCAL_DIR.exists() else []
    if not md_files:
        return {"sync": sync_result, "seed": "skipped (no .md files)"}

    # Point seed_prompts to the GCS-synced directory
    os.environ["PROMPT_TEMPLATES_DIR"] = str(LOCAL_DIR)

    try:
        from app.scripts.seed_prompts import seed_all
        seed_result = seed_all()
        return {"sync": sync_result, "seed": seed_result}
    except Exception as e:
        log.warning(f"Prompt seed failed: {e}")
        return {"sync": sync_result, "seed": f"error: {e}"}


if __name__ == "__main__":
    result = sync_and_seed_prompts()
    log.info(f"Result: {result}")
