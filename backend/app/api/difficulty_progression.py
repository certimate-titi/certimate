"""Difficulty Progression API — 階層式難度遞進。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.difficulty_progression_service import DifficultyProgressionService

router = APIRouter(prefix="/difficulty-progression")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


class NextStrategyRequest(BaseModel):
    current_node_id: str
    original_node_id: Optional[str] = None
    consecutive_wrong: int = 0
    consecutive_correct: int = 0


# ========== Start ==========

@router.post("/subjects/{subject_id}/start")
def start_adaptive(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """start adaptive。

    此 endpoint 對應 `start_adaptive` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = DifficultyProgressionService(db)
    result = service.start_adaptive(user_id, subject_id)
    return _handle_result(result)


# ========== Next Strategy ==========

@router.post("/subjects/{subject_id}/next-strategy")
def next_strategy(
    subject_id: str,
    body: NextStrategyRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """next strategy。

    此 endpoint 對應 `next_strategy` 操作。

    Args:
        subject_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = DifficultyProgressionService(db)
    result = service.calculate_next_strategy(
        user_id=user_id,
        subject_id=subject_id,
        current_node_id=body.current_node_id,
        original_node_id=body.original_node_id,
        consecutive_wrong=body.consecutive_wrong,
        consecutive_correct=body.consecutive_correct,
    )
    return _handle_result(result)


# ========== Trail ==========

@router.get("/subjects/{subject_id}/trail")
def get_trail(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get trail。

    此 endpoint 對應 `get_trail` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = DifficultyProgressionService(db)
    return service.get_trail(user_id, subject_id)
