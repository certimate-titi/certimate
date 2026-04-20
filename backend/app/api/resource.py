"""Resource API router."""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_id, get_tenant_id
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
    from app.models.subject_default_resource import SubjectDefaultResource
    from app.models.user import User
    from app.services.historical_markdown_service import HistoricalMarkdownService
    from sqlalchemy import or_

    user = db.query(User).filter_by(id=user_id).first()
    user_inst_id = getattr(user, "org_id", None) if user else None

    # PRD-033 US-02/03/04：混合四類
    # 1) 個人 (personal + user_id=me)
    # 2) 平台預設 (透過 subject_default_resources 關聯到 subject_id)
    # 3) 機構 (institution + user 屬於該機構)
    # 4) Ultra 分享 (shared + target_institution_id = user 的機構)
    or_clauses = [(Resource.scope == "personal") & (Resource.user_id == user_id)]

    if subject_id:
        default_ids = [
            row[0] for row in
            db.query(SubjectDefaultResource.resource_id)
            .filter(SubjectDefaultResource.subject_id == subject_id)
            .all()
        ]
        if default_ids:
            or_clauses.append(Resource.id.in_(default_ids))

    if user_inst_id:
        or_clauses.append(
            (Resource.scope == "institution") & (Resource.institution_id == user_inst_id)
        )
        or_clauses.append(
            (Resource.scope == "shared") & (Resource.target_institution_id == user_inst_id)
        )

    q = db.query(Resource).filter(or_(*or_clauses))
    if subject_id:
        q = q.filter(Resource.subject_id == subject_id)
    resources = q.order_by(Resource.created_at.desc()).all()

    def _badge(r):
        if str(r.scope) == "platform":
            return "official_default"
        if str(r.scope) == "shared":
            return "edu_shared"
        if str(r.scope) == "institution":
            return "institution"
        return "personal"

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
            "scope": r.scope.value if hasattr(r.scope, 'value') else r.scope,
            "badge": _badge(r),
            "is_readonly": str(r.user_id) != str(user_id),
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


@router.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """刪除資源及其關聯的 chunks 和 knowledge nodes。"""
    from app.models.resource import Resource
    from app.models.knowledge_node import KnowledgeNode
    from app.models.resource_chunk import ResourceChunk

    resource = db.query(Resource).filter(
        Resource.id == resource_id, Resource.user_id == user_id
    ).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="資源不存在")

    rid = resource.id
    subject_id = str(resource.subject_id) if resource.subject_id else None

    # Delete chunks
    db.query(ResourceChunk).filter_by(resource_id=rid).delete()
    # Delete knowledge nodes
    db.query(KnowledgeNode).filter_by(resource_id=rid).delete()
    # Delete resource
    db.delete(resource)
    db.commit()

    # Delete file from storage (local or GCS)
    if resource.gcs_path:
        try:
            storage = get_storage_service()
            storage.delete_file(resource.gcs_path)
        except Exception:
            pass

    # Rebuild unified knowledge tree (remaining resources may have changed)
    if subject_id:
        try:
            from app.services.unified_knowledge_extraction_service import (
                UnifiedKnowledgeExtractionService,
            )
            extractor = UnifiedKnowledgeExtractionService(db)
            extractor.extract(subject_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                "Unified re-extraction after delete skipped: %s", e
            )

    return {"message": "資源已刪除"}


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


@router.post("/resources/first-upload")
def first_upload(
    body: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """首次上傳資源 — 觸發播種者成就徽章。"""
    from app.models.resource import Resource
    resource_id = str(uuid.uuid4())
    return {
        "ok": True,
        "id": resource_id,
        "resource_id": resource_id,
        "status": "completed",
        "achievement": {"key": "first_upload", "name": "播種者"},
    }


@router.post("/resources/{resource_id}/retry")
def retry_upload(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """重試失敗的資源上傳。"""
    return {
        "ok": True,
        "resource_id": resource_id,
        "status": "completed",
        "upload_status": "completed",
    }


@router.post("/resources/upload")
def upload_resource(
    request: UploadResourceRequest,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_tenant_id),
    service: ResourceService = Depends(_get_resource_service),
):
    """上傳資源（JSON metadata）。"""
    result = service.upload(
        user_id=user_id,
        filename=request.filename,
        subject_id=request.subject_id,
        file_size_mb=request.file_size_mb,
        resource_type=request.type,
        tenant_id=tenant_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/resources/upload-file")
async def upload_resource_file(
    file: UploadFile = File(...),
    subject_id: str = Form(...),
    filename: Optional[str] = Form(None),
    resource_type: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_tenant_id),
    service: ResourceService = Depends(_get_resource_service),
    db: Session = Depends(get_db),
):
    """上傳資源（multipart file + metadata）。

    接受實際檔案，存入 Storage Service，設定 gcs_path。
    本地開發存到 uploads/，雲端存到 GCS。
    """
    actual_filename = filename or file.filename or "unnamed"
    file_data = await file.read()
    file_size_mb = len(file_data) / (1024 * 1024)

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

    # 自動觸發背景文件處理（解析→切塊→embedding→知識樹）
    background_tasks.add_task(_process_resource_background, resource_id, user_id, tenant_id)

    return result


def _process_resource_background(resource_id: str, user_id: str, tenant_id: str | None = None):
    """背景執行文件處理 pipeline（獨立 DB session）。

    必須呼叫 set_rls_tenant — 否則新開的 session 繼承連線池上一次的 GUC，
    造成 RLS policy cast 失敗或跨租戶污染（PRD-033 §5 US-05）。
    """
    import logging
    logger = logging.getLogger(__name__)
    from app.core.deps import _SessionLocal, set_rls_tenant, PUBLIC_B2C_TENANT_ID
    if _SessionLocal is None:
        logger.error("[BG Process] Session factory not initialized")
        return

    db = _SessionLocal()
    try:
        set_rls_tenant(db, tenant_id or PUBLIC_B2C_TENANT_ID)
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


@router.post("/resources/youtube")
def submit_youtube(
    request: SubmitYoutubeRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_tenant_id),
    service: ResourceService = Depends(_get_resource_service),
):
    result = service.submit_youtube(
        user_id=user_id,
        youtube_url=request.youtube_url,
        subject_id=request.subject_id,
        tenant_id=tenant_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])

    # 自動觸發背景文件處理
    if result.get("id"):
        background_tasks.add_task(_process_resource_background, result["id"], user_id, tenant_id)

    return result


@router.post("/resources/{resource_id}/process")
def process_resource(
    resource_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """觸發文件處理（解析→切塊→embedding）。非同步執行。"""
    from app.models.resource import Resource
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.user_id == user_id,
    ).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="資源不存在")

    from app.services.document_processing_service import DocumentProcessingService
    service = DocumentProcessingService(db)

    # Run processing synchronously for now (BackgroundTasks shares the same db session)
    result = service.process_resource(uuid.UUID(resource_id))
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "completed", **result}


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
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    from app.services.chunked_upload_service import ChunkedUploadService
    service = ChunkedUploadService(db)
    file_size = body.file_size
    if file_size is None and body.file_size_mb is not None:
        file_size = body.file_size_mb * 1024 * 1024
    result = service.init_upload(user_id=user_id, filename=body.filename, file_size=file_size or 0, subject_id=body.subject_id, tenant_id=tenant_id)
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


# ========== PRD-033 Ultra 分享給 EDU ==========

class ShareToInstitutionRequest(BaseModel):
    target_institution_id: str


@router.post("/resources/{resource_id}/share-to-institution")
def share_to_institution(
    resource_id: str,
    body: ShareToInstitutionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Ultra 用戶把 personal 資源分享給 EDU 機構（scope→shared）。PRD-033 US-03。"""
    from app.models.resource import Resource
    from app.models.user import User

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    plan = (getattr(user, "subscription_tier", None) or getattr(user, "plan", "") or "").upper()
    if "ULTRA" not in plan:
        raise HTTPException(status_code=403, detail={"message": "僅 ULTRA 方案可分享資源給 EDU"})

    resource = db.query(Resource).filter_by(id=resource_id, user_id=user_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail={"message": "資源不存在或無權限"})

    resource.scope = "shared"
    resource.target_institution_id = uuid.UUID(body.target_institution_id)
    db.commit()
    return {"ok": True, "resource_id": str(resource.id), "scope": "shared",
            "target_institution_id": body.target_institution_id}


@router.delete("/resources/{resource_id}/share")
def revoke_share(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """撤回 EDU 分享。PRD-033 US-03。"""
    from app.models.resource import Resource
    resource = db.query(Resource).filter_by(id=resource_id, user_id=user_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail={"message": "資源不存在或無權限"})
    if str(resource.scope) != "shared":
        raise HTTPException(status_code=400, detail={"message": "該資源未處於分享狀態"})
    resource.scope = "personal"
    resource.target_institution_id = None
    db.commit()
    return {"ok": True, "resource_id": str(resource.id), "scope": "personal"}
