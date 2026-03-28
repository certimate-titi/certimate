"""個人儀表板 API。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.get("")
def get_dashboard(
    subject: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    result = service.get_dashboard(user_id=user_id, subject_name=subject)
    return _handle_result(result)


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    age: int | None = None
    education: str | None = None
    career: str | None = None
    daily_study_minutes: int | None = None
    learning_style: str | None = None


@router.patch("/profile")
def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    result = service.update_profile(user_id=user_id, data=body.model_dump(exclude_none=True))
    return _handle_result(result)
