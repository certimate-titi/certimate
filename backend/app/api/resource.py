"""Resource API router."""

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_id
from app.repositories.resource_repository import ResourceRepository
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.repositories.user_repository import UserRepository
from app.services.resource_service import ResourceService
from app.services.knowledge_map_service import KnowledgeMapService
from app.schemas.resource import UploadResourceRequest, SubmitYoutubeRequest

# Local upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter()


def _get_resource_service(db: Session = Depends(get_db)) -> ResourceService:
    return ResourceService(ResourceRepository(db), UserRepository(db))


def _get_knowledge_map_service(db: Session = Depends(get_db)) -> KnowledgeMapService:
    return KnowledgeMapService(ResourceRepository(db), KnowledgeNodeRepository(db))


@router.get("/resources")
def list_resources(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出使用者的所有資源。"""
    repo = ResourceRepository(db)
    from app.models.resource import Resource
    resources = db.query(Resource).filter(Resource.user_id == user_id).order_by(Resource.created_at.desc()).all()
    return {
        "resources": [
            {
                "id": str(r.id),
                "filename": r.name or "",
                "resource_type": r.type.value if hasattr(r.type, 'value') else r.type,
                "status": r.status.value if hasattr(r.status, 'value') else r.status,
                "subject_id": str(r.subject_id) if r.subject_id else None,
                "file_size_mb": round(r.file_size_bytes / (1024 * 1024), 1) if r.file_size_bytes else None,
                "youtube_url": r.youtube_url or "",
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in resources
        ]
    }


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
    # Delete chunks
    db.query(ResourceChunk).filter_by(resource_id=rid).delete()
    # Delete knowledge nodes
    db.query(KnowledgeNode).filter_by(resource_id=rid).delete()
    # Delete resource
    db.delete(resource)
    db.commit()

    # Delete file from disk
    if resource.gcs_path:
        try:
            Path(resource.gcs_path).unlink(missing_ok=True)
        except Exception:
            pass

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


@router.post("/resources/upload")
def upload_resource(
    request: UploadResourceRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResourceService = Depends(_get_resource_service),
):
    """上傳資源（JSON metadata）。"""
    result = service.upload(
        user_id=user_id,
        filename=request.filename,
        subject_id=request.subject_id,
        file_size_mb=request.file_size_mb,
        resource_type=request.type,
    )
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/resources/youtube")
def submit_youtube(
    request: SubmitYoutubeRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResourceService = Depends(_get_resource_service),
):
    result = service.submit_youtube(
        user_id=user_id,
        youtube_url=request.youtube_url,
        subject_id=request.subject_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
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
@router.post("/resources/chunked-upload/init")
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
@router.get("/resources/chunked-upload/{upload_id}/progress")
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
@router.post("/resources/chunked-upload/{upload_id}/complete")
def merge_chunks(
    upload_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    from app.services.chunked_upload_service import ChunkedUploadService
    service = ChunkedUploadService(db)
    result = service.merge_chunks(user_id=user_id, upload_id=upload_id)
    return _handle_chunked_result(result)
