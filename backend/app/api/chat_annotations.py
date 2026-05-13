"""Chat Annotations API — AI 對話 highlight + 評語管理。

Endpoints:
  POST   /api/v1/chat-annotations        201 建立一筆 annotation
  GET    /api/v1/chat-annotations        200 列出自己的 annotations
  DELETE /api/v1/chat-annotations/{id}   204 刪除自己的 annotation
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.schemas.chat_annotation import (
    ChatAnnotationCreate,
    ChatAnnotationListResponse,
    ChatAnnotationResponse,
    ChatAnnotationUpdate,
)
from app.services.chat_annotation_service import ChatAnnotationService

logger = logging.getLogger("certimate.chat_annotations")

router = APIRouter(prefix="/chat-annotations")


def _handle_result(result: dict):
    """Service 層結果轉 HTTPException。"""
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail=result.get("message", "未知錯誤"),
        )
    return result


@router.post("", status_code=201, response_model=ChatAnnotationResponse)
def create_annotation(
    body: ChatAnnotationCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """對 AI 訊息 highlight 並寫評語。

    - 需登入（JWT）
    - user_annotation 最少 10 字（Pydantic + Service 雙重驗）
    - 每個 session 最多 5 筆（超過 409）
    - 只能標記自己的 session（跨 user → 403）
    """
    svc = ChatAnnotationService(db)
    result = svc.create_annotation(
        message_id=body.message_id,
        user_id=UUID(user_id),
        session_id=body.session_id,
        highlighted_text=body.highlighted_text,
        user_annotation=body.user_annotation,
        annotation_type=body.annotation_type,
    )
    _handle_result(result)
    return result["annotation"]


@router.get("", response_model=ChatAnnotationListResponse)
def list_annotations(
    session_id: UUID | None = Query(None, description="可選：只撈該 session 的 annotations"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """列出自己的 annotations（可 filter by session）。"""
    svc = ChatAnnotationService(db)
    result = svc.list_annotations(
        user_id=UUID(user_id),
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    _handle_result(result)
    return {"items": result["items"], "total": result["total"]}


@router.patch("/{annotation_id}", response_model=ChatAnnotationResponse)
def update_annotation(
    annotation_id: UUID,
    body: ChatAnnotationUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """更新自己的 annotation（user_annotation / annotation_type 至少一個）。

    - 不存在 → 404
    - 他人的 → 403
    - user_annotation 若提供必須 ≥ 10 字
    """
    if body.user_annotation is None and body.annotation_type is None:
        raise HTTPException(status_code=422, detail="至少提供 user_annotation 或 annotation_type 其中之一")

    svc = ChatAnnotationService(db)
    result = svc.update_annotation(
        annotation_id=annotation_id,
        user_id=UUID(user_id),
        user_annotation=body.user_annotation,
        annotation_type=body.annotation_type,
    )
    _handle_result(result)
    return result["annotation"]


@router.delete("/{annotation_id}", status_code=204)
def delete_annotation(
    annotation_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """刪除自己的 annotation（他人的 → 403，不存在 → 404）。"""
    svc = ChatAnnotationService(db)
    result = svc.delete_annotation(
        annotation_id=annotation_id,
        user_id=UUID(user_id),
    )
    _handle_result(result)
