"""PRD-034 — Admin Platform Subject management API。

管理員對 platform subject 的版本控制：publish / rollback / list versions。
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id, get_db
from app.services.platform_subject_admin_service import PlatformSubjectAdminService


class DraftUpdateRequest(BaseModel):
    resource_ids: list[str] | None = None

router = APIRouter(prefix="/admin/platform-subjects")


def _handle_result(result: dict):
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result


@router.put("/{subject_id}/draft")
def update_draft(
    subject_id: str,
    body: DraftUpdateRequest,
    _user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """update draft。

    此 endpoint 對應 `update_draft` 操作。

    Args:
        subject_id: 參數。
        body: 參數。
        _user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    return _handle_result(
        PlatformSubjectAdminService(db).update_draft(
            subject_id, resource_ids=body.resource_ids
        )
    )


@router.post("/{subject_id}/publish")
def publish(
    subject_id: str,
    _user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """publish。

    此 endpoint 對應 `publish` 操作。

    Args:
        subject_id: 參數。
        _user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    return _handle_result(PlatformSubjectAdminService(db).publish(subject_id))


@router.post("/{subject_id}/rollback")
def rollback(
    subject_id: str,
    _user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """rollback。

    此 endpoint 對應 `rollback` 操作。

    Args:
        subject_id: 參數。
        _user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    return _handle_result(PlatformSubjectAdminService(db).rollback(subject_id))


@router.get("/{subject_id}/versions")
def list_versions(
    subject_id: str,
    _user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """list versions。

    此 endpoint 對應 `list_versions` 操作。

    Args:
        subject_id: 參數。
        _user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    return _handle_result(PlatformSubjectAdminService(db).list_versions(subject_id))
