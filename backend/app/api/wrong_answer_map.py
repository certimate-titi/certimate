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
    service = WrongAnswerMapService(db)
    return service.get_map(user_id, subject_id, time_range=time_range)


# ========== Node Wrong Answers ==========

@router.get("/nodes/{node_id}/wrong-answers")
def get_node_wrong_answers(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    service = WrongAnswerMapService(db)
    return service.get_node_wrong_answers(user_id, node_id)


# ========== Export Markdown ==========

@router.get("/subjects/{subject_id}/map/markdown")
def export_markdown(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    service = WrongAnswerMapService(db)
    content = service.export_markdown(user_id, subject_id)
    return PlainTextResponse(content=content, media_type="text/markdown")
