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


class EnqueueFailedError(RuntimeError):
    """背景處理排程失敗（Cloud Tasks 與 inline fallback 均無法成功）。

    上游 API endpoint 應 catch 此例外，將 resource 標記為 FAILED 並設 error_message，
    避免 silent PENDING 永遠卡住（Issue #68）。
    """


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

    Raises:
        EnqueueFailedError: 排程失敗（worker 模式下 WORKER_SERVICE_URL 缺失或
            Cloud Tasks 異常）。Issue #68 防止 silent PENDING。
    """
    mode = _get_processor_mode()

    if mode == BackgroundProcessor.INLINE:
        _enqueue_inline(resource_id, user_id)
    else:
        _enqueue_cloud_tasks(resource_id, user_id, tenant_id)


# ── inline fallback ──────────────────────────────────────────────────────────

def _enqueue_inline(resource_id: str, user_id: str) -> None:
    """在背景 thread 直接執行完整 pipeline（本地 dev 用）。

    包含 step 1（chunk+embed+knowledge）+ step 2（K-06 scaffold parse_job），
    與 Cloud Tasks worker handler 對齊；避免 inline 模式漏 step 2 導致本地
    驗收時 scaffold/markdown 沒生成（2026-05-12 YT Layer 2 驗收揭露）。
    """
    import threading

    def _run():
        try:
            from app.core.deps import _SessionLocal
            if _SessionLocal is None:
                logger.error("[inline] Session factory not initialized")
                return
            db = _SessionLocal()
            try:
                import uuid as _uuid
                from app.models.resource import Resource
                from app.services.document_processing_service import DocumentProcessingService

                # Step 1：chunk + embed + knowledge
                svc = DocumentProcessingService(db)
                result = svc.process_resource(_uuid.UUID(resource_id))
                if result.get("error"):
                    logger.error(
                        "[inline] resource=%s step1 failed: %s",
                        resource_id, result.get("message"),
                    )
                    return
                logger.info(
                    "[inline] resource=%s step1 completed: %s chunks",
                    resource_id, result.get("chunks_created", 0),
                )

                # Step 2：K-06 scaffold parse_job（對齊 tasks.py handler）
                try:
                    try:
                        db.rollback()
                    except Exception:
                        pass
                    from app.services.resource_parse_service import (
                        create_parse_job, run_parse_job,
                    )
                    res = db.query(Resource).filter_by(
                        id=_uuid.UUID(resource_id)
                    ).first()
                    has_content = res and (res.gcs_path or res.youtube_url)
                    if has_content:
                        job = create_parse_job(db, res)
                        db.commit()
                        outcome = run_parse_job(db, job.id)
                        db.commit()
                        logger.info(
                            "[inline] resource=%s step2 parse_job=%s status=%s",
                            resource_id, job.id, outcome.status,
                        )
                    else:
                        logger.warning(
                            "[inline] resource=%s step2 SKIPPED (no gcs_path/youtube_url)",
                            resource_id,
                        )
                except Exception as p_exc:
                    logger.exception(
                        "[inline] resource=%s step2 parse_job failed (non-fatal): %s",
                        resource_id, p_exc,
                    )
                    try:
                        db.rollback()
                    except Exception:
                        pass
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
        # Issue #68：worker 模式下 WORKER_SERVICE_URL 必須設定，否則無 silent fallback
        # （inline thread 失敗無觀測性，最終 resource 卡 PENDING 永久）
        logger.error(
            "[cloud_tasks] WORKER_SERVICE_URL 未設定（CRITICAL）— "
            "worker 模式必須在 deploy env 設此變數。raise EnqueueFailedError "
            "讓 API 標記 resource FAILED 給用戶可見錯誤（resource=%s）",
            resource_id,
        )
        raise EnqueueFailedError(
            "背景處理排程失敗：WORKER_SERVICE_URL 未設定。"
            "請聯絡管理員檢查 Cloud Run 環境變數配置。"
        )

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
            # RC7 修補（2026-04-30）：Cloud Run OIDC audience 必須是 service base URL
            # （不含 path），否則 platform 層 audience 校驗 401。target_url 含 path
            # `/api/v1/tasks/process-resource` 不可當 audience。
            task["http_request"]["oidc_token"] = {
                "service_account_email": oidc_sa,
                "audience": worker_url.rstrip("/"),
            }

        response = client.create_task(request={"parent": parent, "task": task})
        logger.info(
            "[cloud_tasks] task created: %s (resource=%s)",
            response.name,
            resource_id,
        )

    except ImportError as ie:
        # Issue #68：worker 模式 SDK 缺失即視為部署問題，不再 silent inline fallback
        logger.error(
            "[cloud_tasks] google-cloud-tasks SDK 未安裝（CRITICAL）— "
            "production 必須在 requirements.txt 含 google-cloud-tasks（resource=%s）: %s",
            resource_id, ie,
        )
        raise EnqueueFailedError(
            "背景處理排程失敗：google-cloud-tasks SDK 未安裝。"
            "請聯絡管理員檢查後端依賴。"
        ) from ie

    except Exception as exc:
        # Issue #68：Cloud Tasks API 失敗（queue 不存在、IAM 拒絕、網路）也應顯式失敗，
        # 不再 fallback 到 inline（fallback 的 thread 失敗無觀測性，最終 PENDING 永久）
        logger.exception(
            "[cloud_tasks] enqueue 失敗（resource=%s）: %s",
            resource_id,
            exc,
        )
        raise EnqueueFailedError(
            f"背景處理排程失敗：Cloud Tasks 異常（{type(exc).__name__}）。"
            "請聯絡管理員檢查 Cloud Tasks queue 設定與 IAM 權限。"
        ) from exc
