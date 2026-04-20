"""Subjects API — 備考科目管理（Onboarding 後）。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.services.onboarding_service import OnboardingService

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
    service = OnboardingService(db)
    result = service.add_subject(user_id=user_id, data=body.model_dump())
    return _handle_result(result)


@router.delete("/{subject_id}")
def remove_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
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
    if not body.confirmed:
        return {"message": "取消移除"}
    service = OnboardingService(db)
    result = service.confirm_remove_subject(user_id=user_id, subject_id=subject_id)
    return _handle_result(result)
