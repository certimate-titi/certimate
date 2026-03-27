"""Resource API router."""

from fastapi import APIRouter, Depends, HTTPException
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
