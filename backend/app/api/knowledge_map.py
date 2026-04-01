"""Knowledge Map API — 知識心智圖導航與 AI 教練。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.services.knowledge_nav_service import KnowledgeNavService

router = APIRouter(prefix="/knowledge-map")


class CoachMessageRequest(BaseModel):
    node_id: str | None = None
    message: str


class SubmitAnswersRequest(BaseModel):
    correct_count: int
    total_count: int


def _handle_result(result: dict):
    """統一處理 service 回傳結果。"""
    if result.get("error"):
        status_code = result.get("status_code", 400)
        resp = {"message": result["message"]}
        for key in ("upgrade", "paywall", "upgrade_prompt", "target_plan"):
            if key in result:
                resp[key] = result[key]
        raise HTTPException(status_code=status_code, detail=resp)
    return result


@router.get("/subjects/{subject_id}/nodes")
def get_nodes_by_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeNavService(db)
    result = service.get_nodes_by_subject(subject_id, user_id)
    return _handle_result(result)


@router.get("/nodes/{node_id}")
def get_node_detail(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeNavService(db)
    result = service.get_node_detail(node_id, user_id)
    return _handle_result(result)


@router.get("/nodes/{node_id}/source")
def get_node_source(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeNavService(db)
    result = service.get_node_source(node_id, user_id)
    return _handle_result(result)


@router.get("/layout")
def get_layout(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeNavService(db)
    result = service.get_layout(user_id)
    return _handle_result(result)


@router.post("/coach/message")
def send_coach_message(
    body: CoachMessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeNavService(db)
    result = service.send_coach_message(body.node_id, body.message, user_id)
    return _handle_result(result)


@router.post("/ai-coach/chat")
def ai_coach_chat(
    body: CoachMessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeNavService(db)
    result = service.send_coach_message(body.node_id, body.message, user_id)
    return _handle_result(result)


class NodeChatRequest(BaseModel):
    message: str


@router.post("/nodes/{node_id}/chat")
def node_chat(
    node_id: str,
    body: NodeChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """節點聊天（前端 knowledge page 使用）。"""
    service = KnowledgeNavService(db)
    result = service.send_coach_message(node_id, body.message, user_id)
    return _handle_result(result)


@router.post("/nodes/{node_id}/submit-answers")
def submit_answers(
    node_id: str,
    body: SubmitAnswersRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeNavService(db)
    result = service.submit_answers(node_id, user_id, body.correct_count, body.total_count)
    return _handle_result(result)
