"""Subjects API — 備考科目管理（Onboarding 後）。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.core.permissions import require_super_admin
from app.models.user import User
from app.services.onboarding_service import OnboardingService
from app.services.bloom_analytics_service import BloomAnalyticsService

router = APIRouter(prefix="/subjects")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.get("/available")
def get_available_subjects(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get available subjects。

    此 endpoint 對應 `get_available_subjects` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = OnboardingService(db)
    result = service.get_available_subjects(user_id=user_id)
    return _handle_result(result)


@router.get("/mine")
def get_my_custom_subjects(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出目前使用者自建的考科（scope=personal AND owner=me）。PRD-033 US-01。"""
    import uuid as _uuid
    from app.models.subject import Subject

    user_uuid = _uuid.UUID(user_id)
    subjects = (
        db.query(Subject)
        .filter(Subject.scope == "personal", Subject.owner_user_id == user_uuid)
        .order_by(Subject.created_at.desc())
        .all()
    )
    return {
        "subjects": [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "category_id": str(s.category_id) if s.category_id else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in subjects
        ]
    }


class AddSubjectRequest(BaseModel):
    subject_name: str
    exam_date: str | None = None
    self_assessed_level: str = "beginner"


@router.post("")
def add_subject(
    body: AddSubjectRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """add subject。

    此 endpoint 對應 `add_subject` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = OnboardingService(db)
    result = service.add_subject(user_id=user_id, data=body.model_dump())
    return _handle_result(result)


@router.post(
    "/{platform_subject_id}/fork-from-platform",
    status_code=status.HTTP_201_CREATED,
)
def fork_from_platform(
    platform_subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """PRD-034 US-01: 從 platform subject 一次性複製資源與心智圖到用戶 personal subject。"""
    from app.services.subject_fork_service import SubjectForkService

    service = SubjectForkService(db)
    result = service.fork_platform_subject(
        user_id=user_id, platform_subject_id=platform_subject_id
    )
    return _handle_result(result)


@router.delete("/{subject_id}")
def remove_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """remove subject。

    此 endpoint 對應 `remove_subject` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = OnboardingService(db)
    result = service.remove_subject(user_id=user_id, subject_id=subject_id)
    return _handle_result(result)


class ConfirmRemoveRequest(BaseModel):
    confirmed: bool = False


@router.post("/{subject_id}/confirm-remove")
def confirm_remove_subject(
    subject_id: str,
    body: ConfirmRemoveRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """confirm remove subject。

    此 endpoint 對應 `confirm_remove_subject` 操作。

    Args:
        subject_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    if not body.confirmed:
        return {"message": "取消移除"}
    service = OnboardingService(db)
    result = service.confirm_remove_subject(user_id=user_id, subject_id=subject_id)
    return _handle_result(result)


@router.get("/{subject_id}/delete-preview")
def get_subject_delete_preview(
    subject_id: str,
    super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """取得刪除 subject 的連帶影響筆數（SUPER_ADMIN only）。

    刪除前呼叫，回傳各子表將連帶刪除的筆數，供前端 modal 顯示警告。

    Returns:
        {
            "subject_id": str,
            "subject_name": str,
            "cascade_count": {
                "exams": int,
                "questions": int,
                "answers": int,
                "resources": int,
                "knowledge_nodes": int,
                "learning_journeys": int,
                ...
            }
        }

    Raises:
        HTTPException 401: JWT 無效
        HTTPException 403: 非 SUPER_ADMIN
        HTTPException 404: subject 不存在
    """
    from app.services.subject_service import SubjectDeleteService
    svc = SubjectDeleteService(db)
    return svc.get_delete_preview(subject_id=subject_id, super_admin=super_admin)


@router.delete("/{subject_id}/hard")
def hard_delete_subject(
    subject_id: str,
    super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """硬刪 subject 及所有連帶資料（SUPER_ADMIN only）。

    此操作不可逆：subject 及其所有 exams、resources、knowledge_nodes、
    learning_journeys、questions、answers 等資料將被永久刪除。

    Returns:
        {"deleted": True, "subject_id": str, "cascade_count": {...}}

    Raises:
        HTTPException 401: JWT 無效
        HTTPException 403: 非 SUPER_ADMIN
        HTTPException 404: subject 不存在
        HTTPException 500: 刪除失敗
    """
    from app.services.subject_service import SubjectDeleteService
    svc = SubjectDeleteService(db)
    return svc.hard_delete_subject(subject_id=subject_id, super_admin=super_admin)


@router.get("/{subject_id}/bloom-distribution")
def get_bloom_distribution(
    subject_id: str,
    trend_by: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Spec 18 — 學科 Bloom 認知層次分佈 / 年度趨勢。

    Query params:
        trend_by: "year" → 回傳各年度趨勢；省略 → 回傳整體分佈

    Returns:
        - 整體分佈 distribution: list of {bloom_category, count, percentage}
        - 年度趨勢 trend: list of {year, remember, understand, ..., create, total}
    """
    service = BloomAnalyticsService(db)
    if trend_by == "year":
        result = service.get_trend_by_year(subject_id)
    else:
        result = service.get_distribution(subject_id)
    return _handle_result(result)
