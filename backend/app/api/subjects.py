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
