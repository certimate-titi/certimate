"""Onboarding API — 首次登入引導。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.get("/status")
def get_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.get_status(user_id=user_id)
    return _handle_result(result)


@router.get("/step/{step}")
def get_step(
    step: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.get_step(user_id=user_id, step=step)
    return _handle_result(result)


class NextStepRequest(BaseModel):
    step: int
    subjects: list = []


@router.post("/next")
def next_step(
    body: NextStepRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.next_step(user_id=user_id, data=body.model_dump())
    return _handle_result(result)


@router.get("/subjects")
def browse_subjects(
    category: str | None = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.browse_subjects(user_id=user_id, category=category)
    return _handle_result(result)


@router.get("/subjects/search")
def search_subjects(
    q: str = Query(""),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.search_subjects(user_id=user_id, query=q)
    return _handle_result(result)


class SubjectInput(BaseModel):
    subject_name: str
    exam_date: str | None = None
    result_date: str | None = None
    self_assessed_level: str = "beginner"


class SubjectsSelectRequest(BaseModel):
    subjects: list[SubjectInput]


@router.post("/subjects")
def select_subjects(
    body: SubjectsSelectRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.select_subjects(
        user_id=user_id,
        subjects_data=[s.model_dump() for s in body.subjects],
    )
    return _handle_result(result)


@router.delete("/subjects/{subject_id}")
def remove_selected_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.remove_selected_subject(user_id=user_id, subject_id=subject_id)
    return _handle_result(result)


class PreferencesRequest(BaseModel):
    daily_study_minutes: int = 30
    learning_preference: str = "mixed"


@router.post("/preferences")
def set_preferences(
    body: PreferencesRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.set_preferences(user_id=user_id, data=body.model_dump())
    return _handle_result(result)


@router.get("/summary")
def get_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.get_summary(user_id=user_id)
    return _handle_result(result)


class OnboardingCompleteRequest(BaseModel):
    display_name: str | None = None
    subjects: list[SubjectInput] = []
    daily_study_minutes: int = 30
    learning_preference: str = "mixed"


@router.post("/complete")
def complete_onboarding(
    body: OnboardingCompleteRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.complete(
        user_id=user_id,
        data=body.model_dump(),
    )
    return _handle_result(result)


@router.post("/subjects/{subject_id}/archive")
def archive_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = OnboardingService(db)
    result = service.archive_subject(user_id=user_id, subject_id=subject_id)
    return _handle_result(result)
