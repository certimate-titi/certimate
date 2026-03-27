"""Community API — 社群歸屬與主動關懷。"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.community_service import CommunityService

router = APIRouter(prefix="/community")


class GenerateReportRequest(BaseModel):
    activities: dict


class ValleyDetectionRequest(BaseModel):
    current_date: str


@router.get("/dashboard")
def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = CommunityService(db)
    return service.get_dashboard(user_id)


@router.post("/weekly-report/generate")
def generate_weekly_reports(
    body: GenerateReportRequest,
    db: Session = Depends(get_db),
):
    service = CommunityService(db)
    return service.generate_weekly_reports(body.activities)


@router.post("/valley-detection/run")
def run_valley_detection(
    body: ValleyDetectionRequest,
    db: Session = Depends(get_db),
):
    service = CommunityService(db)
    return service.run_valley_detection(body.current_date)


@router.get("/exam-results/coaching")
def get_exam_coaching(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = CommunityService(db)
    return service.get_exam_coaching(user_id)
