"""Reverse Engineering API — 考綱逆向工程。"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.reverse_engineering_service import ReverseEngineeringService
from app.services.unified_knowledge_extraction_service import UnifiedKnowledgeExtractionService

router = APIRouter(prefix="/reverse-engineering")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


class ImportMarkdownRequest(BaseModel):
    markdown: str


# ========== 統一知識樹萃取 ==========

@router.post("/subjects/{subject_id}/extract")
def extract_unified_knowledge_tree(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """統一萃取知識樹（合併考古題 + 用戶資源 chunks）。"""
    import logging
    try:
        service = UnifiedKnowledgeExtractionService(db)
        result = service.extract(subject_id)
        return _handle_result(result)
    except Exception as e:
        logging.getLogger("extraction").exception("Extraction error: %s", e)
        raise HTTPException(status_code=500, detail={"message": f"Extraction error: {str(e)}"})


# ========== Trigger (Legacy) ==========

@router.post("/subjects/{subject_id}/trigger")
def trigger_reverse_engineering(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """trigger reverse engineering。

    此 endpoint 對應 `trigger_reverse_engineering` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """trigger incremental。

    此 endpoint 對應 `trigger_incremental` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """get knowledge tree。

    此 endpoint 對應 `get_knowledge_tree` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """export markdown。

    此 endpoint 對應 `export_markdown` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """import markdown。

    此 endpoint 對應 `import_markdown` 操作。

    Args:
        subject_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """get node stats。

    此 endpoint 對應 `get_node_stats` 操作。

    Args:
        node_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """get unmapped questions。

    此 endpoint 對應 `get_unmapped_questions` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
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
    """get quality report。

    此 endpoint 對應 `get_quality_report` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = ReverseEngineeringService(db)
    result = service.get_quality_report(user_id, subject_id)
    return _handle_result(result)
