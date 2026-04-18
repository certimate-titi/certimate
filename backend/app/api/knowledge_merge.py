"""Knowledge Merge API — 知識樹合併對齊。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.knowledge_merge_service import KnowledgeMergeService

router = APIRouter(prefix="/knowledge-merge")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


# ========== Request Schemas ==========


class IncomingNode(BaseModel):
    name: str
    source_origin: str = "document"
    parent_id: Optional[str] = None
    depth: int = 0
    sort_order: int = 0


class MergeRequest(BaseModel):
    incoming_nodes: list[IncomingNode]
    trigger_source: str = "document"
    trigger_name: str = ""


class CompareRequest(BaseModel):
    existing_name: str
    incoming_name: str


class ResolveRequest(BaseModel):
    action: str


# ========== Merge ==========


@router.post("/subjects/{subject_id}/merge")
def trigger_merge(
    subject_id: str,
    body: MergeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeMergeService(db)
    result = service.merge(
        user_id,
        subject_id,
        [n.model_dump() for n in body.incoming_nodes],
        trigger_source=body.trigger_source,
        trigger_name=body.trigger_name,
    )
    return _handle_result(result)


# ========== Compare ==========


@router.post("/subjects/{subject_id}/compare")
def compare_nodes(
    subject_id: str,
    body: CompareRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    score = KnowledgeMergeService.compare_nodes(body.existing_name, body.incoming_name)
    return {"existing_name": body.existing_name, "incoming_name": body.incoming_name, "similarity": round(score, 4)}


# ========== Conflicts ==========


@router.get("/subjects/{subject_id}/conflicts")
def get_conflicts(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeMergeService(db)
    result = service.get_conflicts(user_id, subject_id)
    return _handle_result(result)


@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(
    conflict_id: str,
    body: ResolveRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeMergeService(db)
    result = service.resolve_conflict(user_id, conflict_id, body.action)
    return _handle_result(result)


# ========== History ==========


@router.get("/subjects/{subject_id}/history")
def get_history(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeMergeService(db)
    result = service.get_history(user_id, subject_id)
    return _handle_result(result)


# ========== Node Detail ==========


@router.get("/nodes/{node_id}/detail")
def get_node_detail(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = KnowledgeMergeService(db)
    result = service.get_node_detail(user_id, node_id)
    return _handle_result(result)


