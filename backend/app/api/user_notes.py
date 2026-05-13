"""User Notes API — 使用者自由格式筆記管理（Feature 50 + 52）。

Endpoints:
  POST   /api/v1/user-notes           201 建立筆記
  GET    /api/v1/user-notes           200 列出自己的筆記（支援 ?tag= filter）
  GET    /api/v1/user-notes/tags      200 列出自己所有 hashtag tags + count
  PATCH  /api/v1/user-notes/{id}      200 更新自己的筆記
  DELETE /api/v1/user-notes/all       200 刪除自己所有筆記 {deleted: N}
  DELETE /api/v1/user-notes/{id}      204 刪除自己的筆記
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.schemas.user_note import (
    UserNoteCreate,
    UserNoteListResponse,
    UserNoteResponse,
    UserNoteTagItem,
    UserNoteTagListResponse,
    UserNoteUpdate,
)
from app.services.user_note_service import UserNoteService

logger = logging.getLogger("certimate.user_notes")

router = APIRouter(prefix="/user-notes")


def _handle(result: dict):
    """Service 層結果轉 HTTPException。"""
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail=result.get("message", "未知錯誤"),
        )
    return result


@router.post("", status_code=201, response_model=UserNoteResponse)
def create_note(
    body: UserNoteCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """建立一筆筆記。

    - 需登入（JWT）
    - content 不可為空
    - subject_id 必須存在
    - node_id 若提供，必須屬於該 subject
    """
    svc = UserNoteService(db)
    result = svc.create(
        user_id=UUID(user_id),
        subject_id=body.subject_id,
        node_id=body.node_id,
        title=body.title,
        content=body.content,
    )
    _handle(result)
    return result["note"]


@router.get("/tags", response_model=UserNoteTagListResponse)
def list_tags(
    subject_id: UUID | None = Query(None, description="依科目過濾（只列該 subject notes 的 tags）"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """列出自己所有 hashtag tags + count（per user global）。

    - 需登入（JWT）
    - 可帶 ?subject_id 只列該科目的 notes 用到的 tags
    - 依 count DESC 排序
    """
    svc = UserNoteService(db)
    result = svc.list_user_tags(
        user_id=UUID(user_id),
        subject_id=subject_id,
    )
    _handle(result)
    return {"items": result["items"], "total": result["total"]}


@router.get("", response_model=UserNoteListResponse)
def list_notes(
    subject_id: UUID | None = Query(None, description="依科目過濾"),
    node_id: UUID | None = Query(None, description="依知識節點過濾"),
    tag: str | None = Query(None, description="依 hashtag normalized 字串過濾"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """列出自己的筆記（可選 filter by subject / node / tag），依 updated_at DESC 排序。

    - ?tag=深度學習 → 只回含 #深度學習 的 notes
    """
    svc = UserNoteService(db)
    result = svc.list(
        user_id=UUID(user_id),
        subject_id=subject_id,
        node_id=node_id,
        tag=tag,
        limit=limit,
        offset=offset,
    )
    _handle(result)
    return {"items": result["items"], "total": result["total"]}


@router.delete("/all")
def delete_all_notes(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """刪除當前 user 所有筆記。

    - 需登入（JWT）
    - 無資料時回 {deleted: 0}，不報錯
    """
    svc = UserNoteService(db)
    result = svc.delete_all_for_user(user_id=UUID(user_id))
    _handle(result)
    return {"deleted": result["deleted"]}


@router.patch("/{note_id}", response_model=UserNoteResponse)
def update_note(
    note_id: UUID,
    body: UserNoteUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """更新自己的筆記（title / content 至少提供一個）。

    - 不存在 → 404
    - 他人的 → 403
    - content 更新為空 → 422
    """
    # 至少提供一個欄位
    if body.title is None and body.content is None:
        raise HTTPException(status_code=422, detail="至少提供 title 或 content 其中之一")

    svc = UserNoteService(db)
    result = svc.update(
        note_id=note_id,
        user_id=UUID(user_id),
        title=body.title,
        content=body.content,
    )
    _handle(result)
    return result["note"]


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """刪除自己的筆記。

    - 不存在 → 404
    - 他人的 → 403
    """
    svc = UserNoteService(db)
    result = svc.delete(
        note_id=note_id,
        user_id=UUID(user_id),
    )
    _handle(result)
