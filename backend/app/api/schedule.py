"""Schedule API — 學習記憶排程。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/schedule")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.get("/recommendations")
def get_recommendations(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    result = service.get_recommendations(user_id=user_id)
    return _handle_result(result)


class InitScheduleRequest(BaseModel):
    subject_id: str


@router.post("/init")
def init_schedule(
    body: InitScheduleRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    result = service.init_schedule(user_id=user_id, subject_id=body.subject_id)
    return _handle_result(result)


class CalculateModeRequest(BaseModel):
    subject_id: str
    today: str | None = None


@router.post("/calculate-mode")
def calculate_mode(
    body: CalculateModeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    result = service.calculate_mode(
        user_id=user_id, subject_id=body.subject_id, today_str=body.today
    )
    return _handle_result(result)
