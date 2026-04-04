"""AI 題退場管理 API + 放榜通知排程 API。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.services.retirement_service import RetirementService
from app.services.result_notification_service import ResultNotificationService

router = APIRouter()


def _handle_result(result: dict):
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result


# ── Retirement Scan ─────────────────────────────────────────────────────────

@router.post("/admin/retirement/scan")
def retirement_scan(db: Session = Depends(get_db)):
    service = RetirementService(db)
    result = service.scan()
    return _handle_result(result)


@router.post("/admin/retirement/hard-delete")
def hard_delete_scan(db: Session = Depends(get_db)):
    service = RetirementService(db)
    result = service.hard_delete()
    return _handle_result(result)


@router.post("/admin/retirement/post-result")
def post_result_scan(db: Session = Depends(get_db)):
    service = RetirementService(db)
    result = service.post_result_scan()
    return _handle_result(result)


@router.post("/admin/subjects/recalculate")
def recalculate(db: Session = Depends(get_db)):
    service = RetirementService(db)
    result = service.recalculate_available_questions()
    return _handle_result(result)


# ── Result Notifications ────────────────────────────────────────────────────

@router.post("/admin/notifications/result-day")
def result_day_notifications(db: Session = Depends(get_db)):
    service = ResultNotificationService(db)
    result = service.send_result_day_notifications()
    return _handle_result(result)


@router.post("/admin/notifications/result-reminder")
def result_reminder(db: Session = Depends(get_db)):
    service = ResultNotificationService(db)
    result = service.send_reminder()
    return _handle_result(result)


@router.post("/admin/notifications/result-default")
def result_default(db: Session = Depends(get_db)):
    service = ResultNotificationService(db)
    result = service.process_default()
    return _handle_result(result)


@router.post("/admin/notifications/cross-recommend")
def cross_recommend(db: Session = Depends(get_db)):
    service = ResultNotificationService(db)
    result = service.cross_recommend()
    return _handle_result(result)
