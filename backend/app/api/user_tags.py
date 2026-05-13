"""User Tags API — 跨 3 sources 的 tag 聚合與 filter。

Feature 54：tag 系統涵蓋 3 sources（user_notes / chat_annotations / scaffold user_response）

Endpoints:
  GET  /api/v1/user-tags/aggregate      聚合 3 sources unique tags + count + sources breakdown
  GET  /api/v1/user-tags/items          指定 tag 下所有 3 sources 的混合 items
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.user_tag_aggregate_service import UserTagAggregateService

logger = logging.getLogger("certimate.user_tags")

router = APIRouter(prefix="/user-tags")


def _handle(result: dict):
    """Service 層結果轉 HTTPException。"""
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail=result.get("message", "未知錯誤"),
        )
    return result


@router.get("/aggregate")
def aggregate_tags(
    subject_id: UUID | None = Query(None, description="可選科目過濾"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """聚合 3 sources（user_notes / chat_annotations / scaffold）的 unique tags。

    回傳格式：
    {
      "items": [
        {"normalized": "ai", "display": "AI", "count": 8, "sources": {"note": 5, "annotation": 2, "scaffold": 1}},
        ...
      ],
      "total": N
    }

    - 需登入（JWT）
    - 只回傳自己的 tags（跨 user 隔離）
    - 可選 subject_id filter
    - 依 count DESC 排序
    """
    svc = UserTagAggregateService(db)
    result = svc.aggregate_tags(
        user_id=UUID(user_id),
        subject_id=subject_id,
        limit=limit,
        offset=offset,
    )
    return _handle(result)


@router.get("/items")
def items_by_tag(
    tag: str = Query(..., description="normalized tag（lowercase，不含 #）"),
    subject_id: UUID | None = Query(None, description="可選科目過濾"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """回傳指定 tag 下所有 3 sources 的混合 items。

    回傳格式：
    {
      "items": [
        {"_kind": "note", "_id": "uuid", "content": "...", "subject_id": "uuid", "created_at": "..."},
        {"_kind": "annotation", "_id": "uuid", "content": "...", "subject_id": null, "created_at": "..."},
        {"_kind": "scaffold", "_id": "uuid", "content": "...", "subject_id": "uuid", "created_at": "..."},
        ...
      ],
      "total": N
    }

    - 需登入（JWT）
    - 只回傳自己的 items
    - tag 自動 lowercase 正規化
    - 可選 subject_id filter
    - 依 created_at DESC 排序
    """
    if not tag.strip():
        raise HTTPException(status_code=422, detail="tag 不可為空")

    svc = UserTagAggregateService(db)
    result = svc.items_by_tag(
        user_id=UUID(user_id),
        tag=tag.strip().lower(),
        subject_id=subject_id,
        limit=limit,
        offset=offset,
    )
    return _handle(result)
