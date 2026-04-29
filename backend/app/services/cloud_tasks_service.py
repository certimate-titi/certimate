"""Cloud Tasks Service — 資源處理任務佇列服務.

架構：
    main service → enqueue_process_resource() → Cloud Tasks queue
    Cloud Tasks → POST /api/v1/tasks/process-resource → worker service

環境變數：
    BACKGROUND_PROCESSOR   : worker (預設) | inline
    CLOUD_TASKS_QUEUE_NAME : resource-processing (預設)
    CLOUD_TASKS_LOCATION   : asia-east1 (預設)
    CLOUD_TASKS_PROJECT_ID : certimate-titi (預設)
    WORKER_SERVICE_URL     : worker 服務 base URL
    WORKER_OIDC_SERVICE_ACCOUNT : OIDC 認證用 service account email
"""

import json
import logging
import os
from enum import Enum

logger = logging.getLogger(__name__)


class BackgroundProcessor(str, Enum):
    """背景處理模式。"""

    WORKER = "worker"   # 送 Cloud Tasks（生產預設）
    INLINE = "inline"   # 直接在 thread 執行（本地 dev 加速）


def _get_processor_mode() -> BackgroundProcessor:
    """讀取環境變數，回傳處理模式。預設 worker。"""
    raw = os.environ.get("BACKGROUND_PROCESSOR", "worker").lower()
    try:
        return BackgroundProcessor(raw)
    except ValueError:
        logger.warning("未知的 BACKGROUND_PROCESSOR 值 '%s'，回退至 worker 模式", raw)
        return BackgroundProcessor.WORKER


def enqueue_process_resource(
    resource_id: str,
    user_id: str,
    tenant_id: str,
) -> None:
    """將資源處理任務加入佇列。

    Args:
        resource_id: 資源 UUID 字串。
        user_id: 觸發上傳的使用者 UUID 字串。
        tenant_id: 租戶 UUID 字串（RLS 過濾用）。

    Behaviour:
        - BACKGROUND_PROCESSOR=worker（預設）：送 Cloud Tasks，POST 到 worker URL。
        - BACKGROUND_PROCESSOR=inline：直接在背景 thread 執行 _process_resource_background。
    """
    mode = _get_processor_mode()

    if mode == BackgroundProcessor.INLINE:
        _enqueue_inline(resource_id, user_id)
    else:
        _enqueue_cloud_tasks(resource_id, user_id, tenant_id)


# ── inline fallback ──────────────────────────────────────────────────────────

def _enqueue_inline(resource_id: str, user_id: str) -> None:
    """在背景 thread 直接執行 pipeline（本地 dev 用）。"""
    import threading

    def _run():
        try:
            from app.core.deps import _SessionLocal
            if _SessionLocal is None:
                logger.error("[inline] Session factory not initialized")
                return
            db = _SessionLocal()
            try:
                import uuid
                from app.services.document_processing_service import DocumentProcessingService
                svc = DocumentProcessingService(db)
                result = svc.process_resource(uuid.UUID(resource_id))
                if result.get("error"):
                    logger.error("[inline] resource=%s failed: %s", resource_id, result.get("message"))
                else:
                    logger.info("[inline] resource=%s completed: %s chunks", resource_id, result.get("chunks_created", 0))
            finally:
                db.close()
        except Exception as exc:
            logger.exception("[inline] resource=%s exception: %s", resource_id, exc)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    logger.info("[inline] resource=%s — background thread started", resource_id)


# ── Cloud Tasks enqueue ───────────────────────────────────────────────────────

def _enqueue_cloud_tasks(
    resource_id: str,
    user_id: str,
    tenant_id: str,
) -> None:
    """建立 Cloud Tasks task，POST 到 worker service URL。

    Lazy import google.cloud.tasks_v2 以避免本地 dev 缺 SDK 報錯。
    若 SDK 不存在或任何 GCP 呼叫失敗，記錄 warning 後 fallback 至 inline 模式。
    """
    worker_url = os.environ.get("WORKER_SERVICE_URL", "")
    if not worker_url:
        logger.warning(
            "[cloud_tasks] WORKER_SERVICE_URL 未設定，fallback 至 inline 模式（resource=%s）",
            resource_id,
        )
        _enqueue_inline(resource_id, user_id)
        return

    queue_name = os.environ.get("CLOUD_TASKS_QUEUE_NAME", "resource-processing")
    location = os.environ.get("CLOUD_TASKS_LOCATION", "asia-east1")
    project_id = os.environ.get("CLOUD_TASKS_PROJECT_ID", "certimate-titi")
    oidc_sa = os.environ.get("WORKER_OIDC_SERVICE_ACCOUNT", "")

    target_url = f"{worker_url.rstrip('/')}/api/v1/tasks/process-resource"
    payload = json.dumps(
        {"resource_id": resource_id, "user_id": user_id, "tenant_id": tenant_id}
    ).encode("utf-8")

    try:
        # Lazy import — 不影響本地無 SDK 環境
        from google.cloud import tasks_v2  # type: ignore[import]

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project_id, location, queue_name)

        task: dict = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": target_url,
                "headers": {"Content-Type": "application/json"},
                "body": payload,
            }
        }

        if oidc_sa:
            task["http_request"]["oidc_token"] = {
                "service_account_email": oidc_sa,
                "audience": target_url,
            }

        response = client.create_task(request={"parent": parent, "task": task})
        logger.info(
            "[cloud_tasks] task created: %s (resource=%s)",
            response.name,
            resource_id,
        )

    except ImportError as ie:
        # 升級為 ERROR：production 必須裝 SDK，靜默 fallback 會隱藏部署問題（RC1 經驗）
        logger.error(
            "[cloud_tasks] google-cloud-tasks SDK 未安裝（CRITICAL）— "
            "production 必須在 requirements.txt 含 google-cloud-tasks。"
            "暫時 fallback 至 inline 模式但管線會塞住 main service（resource=%s）: %s",
            resource_id, ie,
        )
        _enqueue_inline(resource_id, user_id)

    except Exception as exc:
        logger.exception(
            "[cloud_tasks] enqueue 失敗，fallback 至 inline 模式（resource=%s）: %s",
            resource_id,
            exc,
        )
        _enqueue_inline(resource_id, user_id)
