"""Resource Library API — 資源庫管理。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.resource_library_service import ResourceLibraryService

router = APIRouter(prefix="/resource-library")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.get("")
def list_resources(
    keyword: str | None = None,
    subject_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出使用者的資源（支援關鍵字 + 科目過濾）。

    Args:
        keyword: 名稱關鍵字（可選）。
        subject_id: 科目 ID 過濾（可選，對應 Spec 11 學科切換器）。
    """
    service = ResourceLibraryService(db)
    result = service.list_resources(user_id=user_id, keyword=keyword, subject_id=subject_id)
    return _handle_result(result)


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """delete resource。

    此 endpoint 對應 `delete_resource` 操作。

    Args:
        resource_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = ResourceLibraryService(db)
    result = service.delete_resource(user_id=user_id, resource_id=resource_id)
    return _handle_result(result)


@router.post("/{resource_id}/reparse")
def reparse_resource(
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """reparse resource。

    此 endpoint 對應 `reparse_resource` 操作。

    Args:
        resource_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = ResourceLibraryService(db)
    result = service.reparse_resource(user_id=user_id, resource_id=resource_id)
    return _handle_result(result)
