"""Resource API router."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.repositories.resource_repository import ResourceRepository
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.repositories.user_repository import UserRepository
from app.services.resource_service import ResourceService
from app.services.knowledge_map_service import KnowledgeMapService
from app.schemas.resource import UploadResourceRequest, SubmitYoutubeRequest

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
                "filename": r.filename or "",
                "resource_type": r.resource_type.value if hasattr(r.resource_type, 'value') else r.resource_type,
                "status": r.status.value if hasattr(r.status, 'value') else r.status,
                "subject_id": str(r.subject_id) if r.subject_id else None,
                "file_size_mb": r.file_size_mb,
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
        "filename": resource.filename or "",
        "resource_type": resource.resource_type.value if hasattr(resource.resource_type, 'value') else resource.resource_type,
        "status": resource.status.value if hasattr(resource.status, 'value') else resource.status,
        "subject_id": str(resource.subject_id) if resource.subject_id else None,
        "file_size_mb": resource.file_size_mb,
        "youtube_url": resource.youtube_url or "",
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
    }


@router.post("/resources/upload")
def upload_resource(
    request: UploadResourceRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResourceService = Depends(_get_resource_service),
):
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
