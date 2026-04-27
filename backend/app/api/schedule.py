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
    """get recommendations。

    此 endpoint 對應 `get_recommendations` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """init schedule。

    此 endpoint 對應 `init_schedule` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """calculate mode。

    此 endpoint 對應 `calculate_mode` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = ScheduleService(db)
    result = service.calculate_mode(
        user_id=user_id, subject_id=body.subject_id, today_str=body.today
    )
    return _handle_result(result)


class RecommendedQuestionsRequest(BaseModel):
    count: int = 10


@router.get("/recommended-questions")
def get_recommended_questions(
    count: int = 10,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """獲取基於掌握度的推薦問題 (使用 MCP Recommendation Server)。"""
    service = ScheduleService(db)
    result = service.get_recommended_questions(user_id=user_id, count=count)
    # 推薦問題可能是空的，但不算錯誤
    return result


class SpacedRepetitionRequest(BaseModel):
    question_id: str


@router.post("/spaced-repetition")
def get_spaced_repetition_schedule(
    body: SpacedRepetitionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """計算艾賓浩斯間隔複習時間 (使用 MCP Recommendation Server)。"""
    service = ScheduleService(db)
    result = service.get_spaced_repetition_schedule(
        user_id=user_id, question_id=body.question_id
    )
    return _handle_result(result)
