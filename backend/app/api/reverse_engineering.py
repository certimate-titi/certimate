"""Reverse Engineering API — 考綱逆向工程。"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.reverse_engineering_service import ReverseEngineeringService

router = APIRouter(prefix="/reverse-engineering")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


class ImportMarkdownRequest(BaseModel):
    markdown: str


# ========== Trigger ==========

@router.post("/subjects/{subject_id}/trigger")
def trigger_reverse_engineering(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ReverseEngineeringService(db)
    result = service.trigger(user_id, subject_id)
    return _handle_result(result)


# ========== Incremental ==========

@router.post("/subjects/{subject_id}/incremental")
def trigger_incremental(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ReverseEngineeringService(db)
    result = service.trigger_incremental(user_id, subject_id)
    return _handle_result(result)


# ========== Knowledge Tree ==========

@router.get("/subjects/{subject_id}/knowledge-tree")
def get_knowledge_tree(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ReverseEngineeringService(db)
    result = service.get_knowledge_tree(user_id, subject_id)
    return _handle_result(result)


# ========== Export Markdown ==========

@router.get("/subjects/{subject_id}/knowledge-tree/markdown")
def export_markdown(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ReverseEngineeringService(db)
    content = service.export_markdown(user_id, subject_id)
    return PlainTextResponse(content=content, media_type="text/markdown")


# ========== Import Markdown ==========

@router.post("/subjects/{subject_id}/import-markdown")
def import_markdown(
    subject_id: str,
    body: ImportMarkdownRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ReverseEngineeringService(db)
    result = service.import_markdown(user_id, subject_id, body.markdown)
    return _handle_result(result)


# ========== Node Stats ==========

@router.get("/nodes/{node_id}/stats")
def get_node_stats(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ReverseEngineeringService(db)
    result = service.get_node_stats(user_id, node_id)
    return _handle_result(result)


# ========== Unmapped Questions ==========

@router.get("/subjects/{subject_id}/unmapped-questions")
def get_unmapped_questions(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ReverseEngineeringService(db)
    result = service.get_unmapped_questions(user_id, subject_id)
    return _handle_result(result)


# ========== Quality Report ==========

@router.get("/subjects/{subject_id}/quality-report")
def get_quality_report(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = ReverseEngineeringService(db)
    result = service.get_quality_report(user_id, subject_id)
    return _handle_result(result)
