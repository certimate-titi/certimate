"""文件解析非同步任務 — 多租戶優先權佇列.

佇列優先級設計：
    paid_priority  —— B2B 機構 + ULTRA_1599（最優先）
    standard       —— PRO_199 / PRO_PLUS_399（標準）
    background     —— FREE（低優先度）

任務類型：
    parse_document_task   — 全文件解析 pipeline（OCR + 結構分析 + Embedding）
    ocr_image_task        — 單圖片 OCR（手寫辨識、圖片資源）
    transcribe_audio_task — 音訊轉文字（STT，YouTube 音訊）

佇列路由規則（worker.py conf.task_routes）：
    app.tasks.document_processing.*  →  依 routing_key 分配

啟動 Worker（各佇列獨立，可水平擴展）：
    # 付費優先佇列（2 個 concurrent）
    .venv/bin/celery -A app.worker worker -Q paid_priority -c 2 --loglevel=info

    # 標準佇列（1 個 concurrent）
    .venv/bin/celery -A app.worker worker -Q standard -c 1 --loglevel=info

    # 背景佇列（1 個 concurrent）
    .venv/bin/celery -A app.worker worker -Q background -c 1 --loglevel=info

    # 或啟動單一 worker 處理全部佇列（開發用）
    .venv/bin/celery -A app.worker worker -Q paid_priority,standard,background --loglevel=info
"""

import logging
import uuid
from typing import Optional

from app.worker import celery_app, QUEUE_PAID_PRIORITY, QUEUE_STANDARD, QUEUE_BACKGROUND

logger = logging.getLogger(__name__)


# ── 佇列選擇 helper ────────────────────────────────────────────────────────────

# 方案 → 佇列映射
_PLAN_TO_QUEUE: dict[str, str] = {
    # B2B（最優先）
    "EDU":            QUEUE_PAID_PRIORITY,
    "INSTITUTION":    QUEUE_PAID_PRIORITY,
    # B2C Ultra（最優先）
    "ULTRA_1599":     QUEUE_PAID_PRIORITY,
    # B2C Pro（標準）
    "PRO_199":        QUEUE_STANDARD,
    "PRO_PLUS_399":   QUEUE_STANDARD,
    # 免費版（背景）
    "FREE":           QUEUE_BACKGROUND,
}


def get_queue_for_plan(plan: Optional[str]) -> str:
    """依用戶訂閱方案決定任務佇列。

    Args:
        plan: 訂閱方案字串（如 "PRO_199"、"EDU"）

    Returns:
        佇列名稱
    """
    if not plan:
        return QUEUE_BACKGROUND
    return _PLAN_TO_QUEUE.get(plan.upper(), QUEUE_BACKGROUND)


def dispatch_document_parse(
    resource_id: str,
    tenant_id: str,
    user_plan: Optional[str] = None,
    *,
    priority_override: Optional[str] = None,
) -> str:
    """派發文件解析任務至對應優先權佇列。

    Args:
        resource_id: Resource UUID
        tenant_id:   租戶 UUID（RLS 隔離用）
        user_plan:   用戶訂閱方案（決定佇列）
        priority_override: 強制指定佇列（管理員用）

    Returns:
        Celery task_id (str)
    """
    queue = priority_override or get_queue_for_plan(user_plan)
    result = parse_document_task.apply_async(
        args=[resource_id, tenant_id],
        queue=queue,
    )
    logger.info(
        "[DocProcessing] dispatched | resource=%s | tenant=%s | plan=%s | queue=%s | task_id=%s",
        resource_id, tenant_id, user_plan, queue, result.id,
    )
    return result.id


def dispatch_ocr_task(
    resource_id: str,
    image_path: str,
    tenant_id: str,
    user_plan: Optional[str] = None,
) -> str:
    """派發 OCR 任務至對應優先權佇列。"""
    queue = get_queue_for_plan(user_plan)
    result = ocr_image_task.apply_async(
        args=[resource_id, image_path, tenant_id],
        queue=queue,
    )
    logger.info(
        "[OCR] dispatched | resource=%s | queue=%s | task_id=%s",
        resource_id, queue, result.id,
    )
    return result.id


def dispatch_transcription_task(
    resource_id: str,
    audio_url: str,
    tenant_id: str,
    user_plan: Optional[str] = None,
) -> str:
    """派發音訊轉文字任務至對應優先權佇列。"""
    queue = get_queue_for_plan(user_plan)
    result = transcribe_audio_task.apply_async(
        args=[resource_id, audio_url, tenant_id],
        queue=queue,
    )
    logger.info(
        "[STT] dispatched | resource=%s | queue=%s | task_id=%s",
        resource_id, queue, result.id,
    )
    return result.id


# ── Celery 任務定義 ────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="app.tasks.document_processing.parse_document_task",
)
def parse_document_task(self, resource_id: str, tenant_id: str):
    """完整文件解析 Pipeline：OCR → 結構分析 → Chunking → Embedding.

    此任務會被路由至 paid_priority / standard / background 其中一個佇列，
    取決於呼叫端使用的 dispatch_document_parse() 函式。
    """
    logger.info("[DocProcessing] start | resource=%s | tenant=%s", resource_id, tenant_id)

    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.core.config import get_settings
        from app.models.resource import Resource, ResourceStatus
        from app.services.document_processing_service import DocumentProcessingService

        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            resource = db.query(Resource).filter(
                Resource.id == uuid.UUID(resource_id),
                Resource.tenant_id == uuid.UUID(tenant_id),  # RLS 隔離
            ).first()

            if not resource:
                logger.error("[DocProcessing] resource not found | resource=%s", resource_id)
                return {"status": "error", "reason": "resource_not_found"}

            # 更新狀態為處理中
            resource.status = ResourceStatus.PROCESSING
            db.commit()

            svc = DocumentProcessingService(db)
            result = svc.process(resource)

            resource.status = ResourceStatus.READY
            db.commit()

            logger.info(
                "[DocProcessing] done | resource=%s | chunks=%d | nodes=%d",
                resource_id,
                result.get("chunk_count", 0),
                result.get("node_count", 0),
            )
            return {"status": "success", **result}

        except Exception as exc:
            db.rollback()
            try:
                from app.models.resource import Resource, ResourceStatus
                r = db.query(Resource).filter(Resource.id == uuid.UUID(resource_id)).first()
                if r:
                    r.status = ResourceStatus.FAILED
                    r.error_message = str(exc)[:500]
                    db.commit()
            except Exception:
                pass
            raise

        finally:
            db.close()

    except Exception as exc:
        logger.error("[DocProcessing] failed | resource=%s | error=%s", resource_id, exc, exc_info=True)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    name="app.tasks.document_processing.ocr_image_task",
)
def ocr_image_task(self, resource_id: str, image_path: str, tenant_id: str):
    """單圖片 OCR 任務（手寫圖片、圖片資源）。

    使用 Claude Vision API 辨識圖片文字。
    """
    logger.info("[OCR] start | resource=%s | image=%s", resource_id, image_path)

    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.core.config import get_settings
        from app.models.resource import Resource
        from app.services.document_processing_service import DocumentProcessingService

        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            resource = db.query(Resource).filter(
                Resource.id == uuid.UUID(resource_id),
                Resource.tenant_id == uuid.UUID(tenant_id),
            ).first()

            if not resource:
                return {"status": "error", "reason": "resource_not_found"}

            svc = DocumentProcessingService(db)
            ocr_text = svc.ocr_image(image_path)

            logger.info("[OCR] done | resource=%s | chars=%d", resource_id, len(ocr_text))
            return {"status": "success", "text_length": len(ocr_text)}

        finally:
            db.close()

    except Exception as exc:
        logger.error("[OCR] failed | resource=%s | error=%s", resource_id, exc, exc_info=True)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=15,
    name="app.tasks.document_processing.transcribe_audio_task",
)
def transcribe_audio_task(self, resource_id: str, audio_url: str, tenant_id: str):
    """音訊轉文字任務（YouTube STT）。

    使用外部 STT 服務轉錄音訊內容。
    """
    logger.info("[STT] start | resource=%s | url=%s", resource_id, audio_url)

    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.core.config import get_settings
        from app.models.resource import Resource

        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            resource = db.query(Resource).filter(
                Resource.id == uuid.UUID(resource_id),
                Resource.tenant_id == uuid.UUID(tenant_id),
            ).first()

            if not resource:
                return {"status": "error", "reason": "resource_not_found"}

            # STT 服務整合（Whisper / Google Speech-to-Text）
            # 目前為框架佔位符，實際 STT 服務在基礎設施就緒後接入
            logger.info("[STT] STT service not yet configured, skipping transcription")
            return {"status": "pending_infrastructure", "reason": "STT service not configured"}

        finally:
            db.close()

    except Exception as exc:
        logger.error("[STT] failed | resource=%s | error=%s", resource_id, exc, exc_info=True)
        raise self.retry(exc=exc)
