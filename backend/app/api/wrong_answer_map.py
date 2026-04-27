"""Wrong Answer Map API — 個人化錯題地圖。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_db_with_tenant, get_current_user_id
from app.services.wrong_answer_map_service import WrongAnswerMapService

router = APIRouter(prefix="/wrong-answer-map")


# ========== Update Mastery ==========

@router.post("/subjects/{subject_id}/update-mastery")
def update_mastery(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """update mastery。

    此 endpoint 對應 `update_mastery` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = WrongAnswerMapService(db)
    return service.update_mastery(user_id, subject_id)


# ========== Get Map ==========

@router.get("/subjects/{subject_id}/map")
def get_map(
    subject_id: str,
    time_range: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """get map。

    此 endpoint 對應 `get_map` 操作。

    Args:
        subject_id: 參數。
        time_range: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = WrongAnswerMapService(db)
    return service.get_map(user_id, subject_id, time_range=time_range)


# ========== Node Wrong Answers ==========

@router.get("/nodes/{node_id}/wrong-answers")
def get_node_wrong_answers(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """get node wrong answers。

    此 endpoint 對應 `get_node_wrong_answers` 操作。

    Args:
        node_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = WrongAnswerMapService(db)
    return service.get_node_wrong_answers(user_id, node_id)


# ========== Export Markdown ==========

@router.post("/subjects/{subject_id}/ai-suggestions")
def get_ai_suggestions(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """依錯題地圖紅色節點產出學習建議（Feature 27 Rule 159）。"""
    service = WrongAnswerMapService(db)
    return service.get_suggestions(user_id, subject_id)


@router.get("/subjects/{subject_id}/map/markdown")
def export_markdown(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """export markdown。

    此 endpoint 對應 `export_markdown` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = WrongAnswerMapService(db)
    content = service.export_markdown(user_id, subject_id)
    return PlainTextResponse(content=content, media_type="text/markdown")
