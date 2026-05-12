"""Resource API router."""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_id, get_current_user_with_tenant, get_tenant_id, PUBLIC_B2C_TENANT_ID
from app.repositories.resource_repository import ResourceRepository
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.repositories.user_repository import UserRepository
from app.services.resource_service import ResourceService
from app.services.knowledge_map_service import KnowledgeMapService
from app.services.storage_service import get_storage_service
from app.schemas.resource import UploadResourceRequest, SubmitYoutubeRequest

router = APIRouter()


def _get_resource_service(db: Session = Depends(get_db)) -> ResourceService:
    return ResourceService(ResourceRepository(db), UserRepository(db))


def _get_knowledge_map_service(db: Session = Depends(get_db)) -> KnowledgeMapService:
    return KnowledgeMapService(ResourceRepository(db), KnowledgeNodeRepository(db))


@router.get("/resources")
def list_resources(
    subject_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出使用者的所有資源。

    若提供 subject_id，會額外把該科目預載的考古題以虛擬資源（type=historical_exam）形式合併回傳。
    """
    from app.models.resource import Resource
    from app.services.historical_markdown_service import HistoricalMarkdownService

    q = db.query(Resource).filter(Resource.user_id == user_id)
    if subject_id:
        q = q.filter(Resource.subject_id == subject_id)
    resources = q.order_by(Resource.created_at.desc()).all()

    items = [
        {
            "id": str(r.id),
            "filename": r.name or "",
            "resource_type": r.type.value if hasattr(r.type, 'value') else r.type,
            "status": r.status.value if hasattr(r.status, 'value') else r.status,
            "subject_id": str(r.subject_id) if r.subject_id else None,
            "file_size_mb": round(r.file_size_bytes / (1024 * 1024), 1) if r.file_size_bytes else None,
            "youtube_url": r.youtube_url or "",
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "error_message": getattr(r, "error_message", None),
        }
        for r in resources
    ]

    if subject_id:
        try:
            historical = HistoricalMarkdownService(db).list_for_subject(subject_id)
            for h in historical:
                items.append({
                    "id": f"hist:{h['id']}",
                    "filename": h["name"],
                    "resource_type": "historical_exam",
                    "status": "ready",
                    "subject_id": subject_id,
                    "file_size_mb": None,
                    "youtube_url": "",
                    "created_at": None,
                    "historical_exam_id": h["id"],
                    "total_questions": h["total_questions"],
                    "year": h["year"],
                })
        except Exception:
            pass

    return {"resources": items}


@router.get("/resources/historical/{historical_exam_id}/markdown")
def get_historical_markdown(
    historical_exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """動態 render 單場考古題為 markdown 字串。"""
    from app.services.historical_markdown_service import HistoricalMarkdownService
    result = HistoricalMarkdownService(db).render_markdown(historical_exam_id)
    if result.get("error"):
        raise HTTPException(status_code=result.get("status_code", 400), detail={"message": result["message"]})
    return result


@router.get("/resources/{resource_id}")
def get_resource(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得單一資源詳情。"""
    from app.models.resource import Resource
    resource = db.query(Resource).filter(Resource.id == resource_id, Resource.user_id == user_id).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="資源不存在")
    return {
        "id": str(resource.id),
        "filename": resource.name or "",
        "resource_type": resource.type.value if hasattr(resource.type, 'value') else resource.type,
        "status": resource.status.value if hasattr(resource.status, 'value') else resource.status,
        "subject_id": str(resource.subject_id) if resource.subject_id else None,
        "file_size_mb": round(resource.file_size_bytes / (1024 * 1024), 1) if resource.file_size_bytes else None,
        "youtube_url": resource.youtube_url or "",
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
    }


@router.get("/resources/{resource_id}/chunks")
def get_resource_chunks(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得資源的所有分塊內容（供知識庫左側 accordion 展開顯示）。

    權限混合模型：
    - 自己上傳的資源 → 直接放行
    - seed 資源（系統建立） → 驗證用戶擁有該 subject
    - 他人上傳的資源 → 403
    """
    from app.models.resource import Resource
    from app.models.resource_chunk import ResourceChunk
    from app.models.learning_journey import LearningJourney

    SEED_USER_ID = "00000000-0000-0000-0000-000000000001"

    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="資源不存在")

    if str(resource.user_id) == user_id:
        pass  # 自己上傳 → 放行
    elif str(resource.user_id) == SEED_USER_ID:
        # seed 資源 → 驗證 subject 歸屬
        has_subject = db.query(LearningJourney).filter(
            LearningJourney.user_id == uuid.UUID(user_id),
            LearningJourney.subject_id == resource.subject_id,
        ).first()
        if has_subject is None:
            raise HTTPException(status_code=403, detail="無權存取此資源")
    else:
        raise HTTPException(status_code=403, detail="無權存取此資源")

    chunks = db.query(ResourceChunk).filter(
        ResourceChunk.resource_id == uuid.UUID(resource_id)
    ).order_by(ResourceChunk.chunk_index).all()

    return {
        "resource_id": resource_id,
        "total_chunks": len(chunks),
        "chunks": [
            {
                "id": str(c.id),
                "chunk_index": c.chunk_index,
                "content": c.content,
                "token_count": c.token_count,
                "source_page_start": c.source_page_start,
                "source_page_end": c.source_page_end,
                "section_title": (c.metadata_json or {}).get("section_title", ""),
                "depth": (c.metadata_json or {}).get("depth", 1),
                "chunk_type": (c.metadata_json or {}).get("chunk_type", "text"),
            }
            for c in chunks
        ],
    }


@router.get("/resources/{resource_id}/delete-preview")
def get_resource_delete_preview(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得刪除 resource 的連帶影響筆數（擁有者 only）。

    刪除前呼叫，回傳各子表將連帶刪除的筆數，供前端 modal 顯示警告。

    Returns:
        {
            "resource_id": str,
            "resource_name": str,
            "cascade_count": {
                "resource_chunks": int,
                "resource_parse_jobs": int,
                "resource_scaffolds": int,
                "question_candidates": int,
                "knowledge_nodes": int,
                ...
            }
        }

    Raises:
        HTTPException 401: JWT 無效
        HTTPException 404: resource 不存在或非本人擁有
    """
    from app.services.subject_service import ResourceDeleteService
    svc = ResourceDeleteService(db)
    return svc.get_delete_preview(resource_id=resource_id, user_id=user_id)


@router.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """硬刪資源及所有連帶子資料（擁有者 only）。

    子表（resource_chunks, resource_parse_jobs, resource_scaffolds,
    question_candidates, knowledge_nodes）透過 DB FK CASCADE 自動清除。
    GCS 檔案同步刪除（非阻斷性）。

    Returns:
        {"deleted": True, "resource_id": str, "cascade_count": {...}}

    Raises:
        HTTPException 401: JWT 無效
        HTTPException 404: resource 不存在或非本人擁有
        HTTPException 500: 刪除失敗
    """
    from app.services.subject_service import ResourceDeleteService
    svc = ResourceDeleteService(db)
    result = svc.hard_delete_resource(resource_id=resource_id, user_id=user_id)

    # 刪除後嘗試重建 unified knowledge tree（非阻斷性）
    import logging
    _logger = logging.getLogger(__name__)
    try:
        from app.models.resource import Resource as _Resource
        # resource 已刪，從 result 無法取 subject_id；
        # ResourceDeleteService 不儲存 subject_id，需獨立查。
        # 此時 resource 已不在 DB，跳過重建（可接受，前端刷新即可）
        pass
    except Exception as exc:
        _logger.warning("Post-delete re-extraction skipped: %s", exc)

    return result


def _process_in_background(resource_id: str, db_url: str):
    """在背景 thread 中執行文件解析（獨立 DB session）。"""
    import threading
    import logging
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    logger = logging.getLogger(__name__)

    def _run():
        try:
            engine = create_engine(db_url, pool_pre_ping=True)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            try:
                from app.services.document_processing_service import DocumentProcessingService
                svc = DocumentProcessingService(session)
                result = svc.process_resource(uuid.UUID(resource_id))
                logger.info("Background processing done for %s: %s", resource_id, result)
            finally:
                session.close()
                engine.dispose()
        except Exception as e:
            logger.exception("Background processing failed for %s: %s", resource_id, e)

    t = threading.Thread(target=_run, daemon=True)
    t.start()


@router.post("/resources/upload-file", status_code=202)
async def upload_resource_file(
    file: UploadFile = File(...),
    subject_id: str = Form(...),
    filename: Optional[str] = Form(None),
    resource_type: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_tenant_id),
    service: ResourceService = Depends(_get_resource_service),
    db: Session = Depends(get_db),
):
    """上傳資源（multipart file + metadata）。

    接受實際檔案，存入 Storage Service，設定 gcs_path。
    本地開發存到 uploads/，雲端存到 GCS。
    回傳 202 Accepted：資源已建立，處理工作已送至背景佇列。

    Issue #68：背景排程失敗即標記 FAILED 並回 503（不再 silent PENDING）。
    """
    from app.services.cloud_tasks_service import (
        EnqueueFailedError,
        enqueue_process_resource,
    )

    actual_filename = filename or file.filename or "unnamed"
    file_data = await file.read()
    file_size_mb = len(file_data) / (1024 * 1024)

    # ────────────────────────────────────────────────────────────────
    # 月度上傳配額檢查（FREE 5/月、PRO 50/月、PRO_PLUS 200/月、ULTRA 無限）
    # 配額消耗=每次上傳成功（會跑 multimodal Pro 解析）。
    # 2026-05-08：reparse 端點下架後，此處變成唯一觸發點。
    # ────────────────────────────────────────────────────────────────
    from app.services.resource_parse_quota_service import (
        check_and_consume, QuotaExceededError,
    )
    from app.models.user import User
    user_obj = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if user_obj is None:
        raise HTTPException(status_code=401, detail={"message": "未授權"})
    try:
        check_and_consume(db, user_obj)
    except QuotaExceededError as exc:
        raise HTTPException(
            status_code=402,
            detail={
                "message": str(exc),
                "limit": exc.limit,
                "used": exc.used,
                "plan": exc.plan,
                "upgrade_hint": "升級 PRO 可用 50 份 / 月",
            },
        )

    # ────────────────────────────────────────────────────────────────
    # 同步預檢（PDF magic bytes + 版權關鍵字）— 失敗則完全不建 Resource row
    # 對應 Feature 02 Rule「上傳時同步預檢 PDF」。
    # ────────────────────────────────────────────────────────────────
    if (resource_type or "").lower() == "pdf":
        if not file_data.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail={"message": "PDF 檔案損毀或無法解析"},
            )
        try:
            from app.services.document_processing_service import DocumentProcessingService
            DocumentProcessingService(db)._check_copyright(file_data)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)})

    # 先做驗證（用原有 service）
    result = service.upload(
        user_id=user_id,
        filename=actual_filename,
        subject_id=subject_id,
        file_size_mb=file_size_mb,
        resource_type=resource_type,
        tenant_id=tenant_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])

    resource_id = result["id"]

    # 存入 Storage Service
    storage = get_storage_service()
    storage_path = storage.save_file(
        user_id=user_id,
        resource_id=resource_id,
        filename=actual_filename,
        data=file_data,
    )

    # 更新 Resource 的 gcs_path
    from app.models.resource import Resource
    resource = db.query(Resource).filter_by(id=uuid.UUID(resource_id)).first()
    if resource:
        resource.gcs_path = storage_path
        resource.file_size_bytes = len(file_data)
        db.commit()

    result["gcs_path"] = storage_path
    result["file_size_bytes"] = len(file_data)

    # 送至 Cloud Tasks（或 inline fallback — 依 BACKGROUND_PROCESSOR env 決定）
    # F31 修補：tenant_id 從 JWT 解析（get_tenant_id DI），不再硬編碼 B2C 預設
    # Issue #68：失敗即標記 FAILED，避免 silent PENDING
    try:
        enqueue_process_resource(
            resource_id=resource_id,
            user_id=user_id,
            tenant_id=tenant_id or PUBLIC_B2C_TENANT_ID,
        )
    except EnqueueFailedError as exc:
        _mark_resource_failed(db, resource_id, str(exc))
        raise HTTPException(
            status_code=503,
            detail={"message": str(exc), "resource_id": resource_id},
        ) from exc

    return result


def _process_resource_background(resource_id: str, user_id: str):
    """背景執行文件處理 pipeline（獨立 DB session）。"""
    import logging
    logger = logging.getLogger(__name__)
    from app.core.deps import _SessionLocal
    if _SessionLocal is None:
        logger.error("[BG Process] Session factory not initialized")
        return

    db = _SessionLocal()
    try:
        from app.services.document_processing_service import DocumentProcessingService
        svc = DocumentProcessingService(db)
        result = svc.process_resource(uuid.UUID(resource_id))
        if result.get("error"):
            logger.error(f"[BG Process] resource={resource_id} failed: {result.get('message')}")
        else:
            logger.info(f"[BG Process] resource={resource_id} completed: {result.get('chunks_created', 0)} chunks")
    except Exception as e:
        logger.exception(f"[BG Process] resource={resource_id} exception: {e}")
    finally:
        db.close()


@router.post("/resources/youtube", status_code=202)
def submit_youtube(
    request: SubmitYoutubeRequest,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_tenant_id),
    service: ResourceService = Depends(_get_resource_service),
    db: Session = Depends(get_db),
):
    """提交 YouTube URL 資源。回傳 202 Accepted，處理工作已送至背景佇列。

    F47 雙路徑分流：
    1. probe metadata（yt-dlp info dict，不下載 audio）取 duration + has_cc
    2. 依 has_cc 套用對應長度上限（有 CC 60 分 / 無 CC 20 分）
    3. 依 has_cc reserve 配額（有 CC=1 份 / 無 CC=5 份）
    4. 無 CC 路徑月度成本封頂檢查（PRO USD 3 / PRO_PLUS USD 12）
    5. enqueue（EnqueueFailedError → refund）
    Issue #68：若背景排程失敗立刻標記 FAILED 並回 503。
    """
    from app.services.cloud_tasks_service import (
        EnqueueFailedError,
        enqueue_process_resource,
    )
    from app.services.resource_parse_quota_service import (
        QuotaExceededError,
        YOUTUBE_QUOTA_COST_WITH_CC,
        YOUTUBE_QUOTA_COST_WITHOUT_CC,
        reserve_youtube_quota,
        refund_quota,
    )
    from app.models.user import User

    # ── 載入 user obj（配額需要） ────────────────────────────────────────
    user_obj = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if user_obj is None:
        raise HTTPException(status_code=401, detail={"message": "未授權"})

    # ── Step 1: probe metadata（yt-dlp 不下載 audio）────────────────────
    duration_minutes, has_cc = _probe_youtube_metadata(request.youtube_url)

    # ── Step 2: 依 has_cc 套用長度上限（有 CC=60 分 / 無 CC=20 分）────────
    if has_cc:
        duration_limit = 60
    else:
        duration_limit = 20

    if duration_minutes is not None and duration_minutes > duration_limit:
        raise HTTPException(
            status_code=422,
            detail={
                "message": (
                    f"YouTube 影片不可超過 {duration_limit} 分鐘"
                    f"（{'有' if has_cc else '無'} CC 上限 {duration_limit} 分，"
                    f"影片 {duration_minutes:.0f} 分鐘超過上限）"
                ),
                "duration_minutes": duration_minutes,
                "has_cc": has_cc,
                "limit_minutes": duration_limit,
            },
        )

    # ── Step 3: 配額預檢（依 has_cc 取 1 或 5 份，只檢查不扣）────────────
    quota_cost = YOUTUBE_QUOTA_COST_WITH_CC if has_cc else YOUTUBE_QUOTA_COST_WITHOUT_CC
    try:
        reserve_youtube_quota(db, user_obj, has_cc=has_cc)  # 不傳 resource_id = 只預檢
    except QuotaExceededError as exc:
        raise HTTPException(
            status_code=402,
            detail={
                "message": str(exc),
                "limit": exc.limit,
                "used": exc.used,
                "plan": exc.plan,
                "upgrade_hint": "升級 PRO 可用 50 份 / 月",
            },
        )

    # ── Step 4: 無 CC 路徑月度成本封頂（PRO USD 3 / PRO_PLUS USD 12）────
    if not has_cc:
        _check_monthly_cost_cap(db, user_obj, request.youtube_url)

    result = service.submit_youtube(
        user_id=user_id,
        youtube_url=request.youtube_url,
        subject_id=request.subject_id,
        tenant_id=tenant_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])

    # ── 配額佔位（插入 stub ParseJob，計入本月用量）────────────────────
    resource_id = result.get("id")
    if resource_id:
        reserve_youtube_quota(
            db, user_obj,
            resource_id=resource_id,
            tenant_id=tenant_id or PUBLIC_B2C_TENANT_ID,
            skip_check=True,  # 已在上方預檢，只插入 stub rows
            has_cc=has_cc,
        )

    # 送至 Cloud Tasks（或 inline fallback）— 失敗即標記 FAILED 顯式回報
    if resource_id:
        try:
            enqueue_process_resource(
                resource_id=resource_id,
                user_id=user_id,
                tenant_id=tenant_id or PUBLIC_B2C_TENANT_ID,
            )
        except EnqueueFailedError as exc:
            _mark_resource_failed(db, resource_id, str(exc))
            # 退回配額（把 stub jobs 標記 FAILED）
            try:
                refund_quota(db, uuid.UUID(user_id), uuid.UUID(resource_id))
            except Exception:
                pass
            raise HTTPException(
                status_code=503,
                detail={"message": str(exc), "resource_id": resource_id},
            ) from exc

    return result


def _probe_youtube_metadata(youtube_url: str) -> tuple[float | None, bool]:
    """使用 yt-dlp（download=False）probe YouTube metadata，回傳 (duration_minutes, has_cc)。

    has_cc = True 若 subtitles 或 automatic_captions 任一非空。
    若 yt-dlp 不可用或 probe 失敗，fallback 回 (None, False)（寬鬆放行）。
    """
    try:
        from app.services.media_extractors.youtube_extractor import probe_youtube_metadata
        meta = probe_youtube_metadata(youtube_url)
        duration_minutes = (meta.duration_seconds / 60.0) if meta.duration_seconds else None
        return duration_minutes, meta.has_cc
    except Exception:
        return None, False


# 月度成本封頂（無 CC 路徑）— 依訂閱方案
_MONTHLY_COST_CAP_USD: dict[str, float] = {
    "PRO": 3.0,
    "PRO_PLUS": 12.0,
}

# 每分鐘 Gemini Pro 預估成本（粗估；詳細定價見 finance TODO）
_GEMINI_PRO_COST_PER_MINUTE_USD = 0.03


def _check_monthly_cost_cap(db: Session, user: object, youtube_url: str) -> None:
    """無 CC 路徑月度成本封頂檢查。

    查詢 ai_usage_ledger 本月累積成本，加上本次預估成本，若超過方案上限回 422。
    若 ai_usage_ledger schema 不支援查詢，記 warning 並放行（best-effort）。

    TODO: finance 確認實際 Gemini Pro 定價後調整 _GEMINI_PRO_COST_PER_MINUTE_USD。
    """
    import logging as _logging

    raw_plan = getattr(user, "subscription_plan", None)
    plan = getattr(raw_plan, "value", raw_plan) or "FREE"
    cap = _MONTHLY_COST_CAP_USD.get(plan)
    if cap is None:
        # FREE / ULTRA 無月度成本封頂（ULTRA 無限，FREE 走配額數量管控）
        return

    try:
        from decimal import Decimal
        from sqlalchemy import text as _text
        from datetime import datetime, timezone

        month_start = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        user_id = getattr(user, "id", None)

        result = db.execute(
            _text(
                "SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage_ledger "
                "WHERE user_id = :uid AND created_at >= :since"
            ),
            {"uid": str(user_id), "since": month_start},
        ).scalar()

        used_usd = float(result or 0)
        # 粗估本次成本（以 20 分鐘上限 * 單價）
        estimated_cost = 20.0 * _GEMINI_PRO_COST_PER_MINUTE_USD

        if used_usd + estimated_cost > cap:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": (
                        f"本月 AI 成本已接近方案上限（{plan} 上限 USD {cap:.0f}，"
                        f"已用 USD {used_usd:.2f}），無 CC 影片處理暫時停用"
                    ),
                    "used_usd": used_usd,
                    "cap_usd": cap,
                    "plan": plan,
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        _logging.getLogger(__name__).warning(
            "月度成本封頂查詢失敗（best-effort 放行）: %s — TODO: finance 確認 ai_usage_ledger schema",
            exc,
        )


def _mark_resource_failed(db: Session, resource_id: str, error_message: str) -> None:
    """Issue #68：背景排程失敗時把 resource 標記 FAILED 並寫入 error_message，
    給前端 UI 與後續查詢可見錯誤（避免 silent PENDING）。"""
    from app.models.resource import Resource, ResourceStatus
    import uuid as _uuid
    try:
        res = db.query(Resource).filter_by(id=_uuid.UUID(resource_id)).first()
        if res:
            res.status = ResourceStatus.FAILED
            res.error_message = error_message
            db.commit()
    except Exception:
        db.rollback()


@router.post("/resources/{resource_id}/process")
def process_resource(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """觸發文件處理（解析→切塊→embedding）。非同步執行，立即回 202 queued。
    F02 修補（2026-05-01）：改非同步避免 500（gcs_path 未設等情境）。
    走既有 cloud_tasks_service.enqueue_process_resource 路徑（與 upload-file 一致）。
    """
    from app.models.resource import Resource
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.user_id == user_id,
    ).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="資源不存在")

    # Issue #68：背景排程失敗即標記 FAILED + 回 503
    from app.services.cloud_tasks_service import (
        EnqueueFailedError,
        enqueue_process_resource,
    )
    try:
        enqueue_process_resource(
            resource_id=resource_id,
            user_id=user_id,
            tenant_id=tenant_id or PUBLIC_B2C_TENANT_ID,
        )
    except EnqueueFailedError as exc:
        _mark_resource_failed(db, resource_id, str(exc))
        raise HTTPException(
            status_code=503,
            detail={"message": str(exc), "resource_id": resource_id},
        ) from exc
    return {"status": "queued", "resource_id": resource_id}


@router.post("/resources/{resource_id}/complete-parsing")
def complete_parsing(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    service: KnowledgeMapService = Depends(_get_knowledge_map_service),
):
    result = service.complete_parsing(resource_id=resource_id, user_id=user_id)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/resources/{resource_id}/generate-map")
def generate_map(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    service: KnowledgeMapService = Depends(_get_knowledge_map_service),
):
    result = service.generate_map(resource_id=resource_id, user_id=user_id)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


# ========== Chunked Upload (ULTRA only) ==========

class InitChunkedUploadRequest(BaseModel):
    filename: str
    file_size: int | None = None
    file_size_mb: int | None = None
    subject_id: str | None = None


def _handle_chunked_result(result: dict):
    if result.get("error"):
        raise HTTPException(status_code=result.get("status_code", 400), detail={"message": result["message"]})
    return result


@router.post("/resources/chunked/init")
def init_chunked_upload(
    body: InitChunkedUploadRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    from app.services.chunked_upload_service import ChunkedUploadService
    service = ChunkedUploadService(db)
    file_size = body.file_size
    if file_size is None and body.file_size_mb is not None:
        file_size = body.file_size_mb * 1024 * 1024
    result = service.init_upload(user_id=user_id, filename=body.filename, file_size=file_size or 0, subject_id=body.subject_id)
    return _handle_chunked_result(result)


@router.post("/resources/chunked/{upload_id}/chunk/{chunk_index}")
async def upload_chunk(
    upload_id: str,
    chunk_index: int,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    from app.services.chunked_upload_service import ChunkedUploadService
    chunk_data = await file.read()
    service = ChunkedUploadService(db)
    result = service.upload_chunk(user_id=user_id, upload_id=upload_id, chunk_index=chunk_index, chunk_data=chunk_data)
    return _handle_chunked_result(result)


@router.get("/resources/chunked/{upload_id}/status")
def get_chunked_upload_status(
    upload_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    from app.services.chunked_upload_service import ChunkedUploadService
    service = ChunkedUploadService(db)
    result = service.get_upload_status(user_id=user_id, upload_id=upload_id)
    return _handle_chunked_result(result)


@router.post("/resources/chunked/{upload_id}/merge")
def merge_chunks(
    upload_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    from app.services.chunked_upload_service import ChunkedUploadService
    service = ChunkedUploadService(db)
    result = service.merge_chunks(user_id=user_id, upload_id=upload_id)
    return _handle_chunked_result(result)
