"""學習歷程 API — 考試結果確認。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.services.learning_journey_service import LearningJourneyService

router = APIRouter(prefix="/learning-journeys")


def _handle_result(result: dict):
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result


@router.get("/pending")
def list_pending(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """list pending。

    此 endpoint 對應 `list_pending` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = LearningJourneyService(db)
    result = service.list_pending(user_id=user_id)
    return _handle_result(result)


class ExamResultRequest(BaseModel):
    status: str


@router.post("/{journey_id}/exam-result")
def confirm_exam_result(
    journey_id: str,
    body: ExamResultRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """confirm exam result。

    此 endpoint 對應 `confirm_exam_result` 操作。

    Args:
        journey_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = LearningJourneyService(db)
    result = service.confirm_exam_result(
        journey_id=journey_id,
        status=body.status,
    )
    return _handle_result(result)


class RetakeRequest(BaseModel):
    exam_date: Optional[str] = None
    result_date: Optional[str] = None


@router.post("/{journey_id}/retake")
def retake(
    journey_id: str,
    body: RetakeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """retake。

    此 endpoint 對應 `retake` 操作。

    Args:
        journey_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = LearningJourneyService(db)
    result = service.retake(
        journey_id=journey_id,
        exam_date=body.exam_date,
        result_date=body.result_date,
    )
    return _handle_result(result)


@router.post("/{journey_id}/quit")
def quit_subject(
    journey_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """quit subject。

    此 endpoint 對應 `quit_subject` 操作。

    Args:
        journey_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = LearningJourneyService(db)
    result = service.quit(journey_id=journey_id)
    return _handle_result(result)


class ResultDateRequest(BaseModel):
    result_date: str


@router.put("/{journey_id}/result-date")
def update_result_date(
    journey_id: str,
    body: ResultDateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """update result date。

    此 endpoint 對應 `update_result_date` 操作。

    Args:
        journey_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = LearningJourneyService(db)
    result = service.update_result_date(
        journey_id=journey_id,
        result_date=body.result_date,
    )
    return _handle_result(result)
