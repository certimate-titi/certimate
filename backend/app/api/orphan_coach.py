"""Orphan Coach API — AI 蘇格拉底教練對話端點.

#9 AI 教練回應 Orphan 節點（蘇格拉底對話）。

端點：
  POST /api/v1/orphan-coach/conversations         啟動對話
  POST /api/v1/orphan-coach/conversations/{cid}/messages  發送訊息
  GET  /api/v1/orphan-coach/conversations/{cid}   取得對話詳情
  GET  /api/v1/orphan-coach/conversations         查詢進行中對話（接續用）
  POST /api/v1/orphan-coach/conversations/{cid}/pause  暫停對話
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.orphan_coach_service import OrphanCoachService

logger = logging.getLogger("certimate.orphan_coach_api")

router = APIRouter(prefix="/orphan-coach")


# ── Pydantic Schemas ───────────────────────────────────────────────

class StartConversationRequest(BaseModel):
    """啟動蘇格拉底對話請求。"""
    model_config = ConfigDict(from_attributes=True)
    node_id: str


class SendMessageRequest(BaseModel):
    """發送對話訊息請求。"""
    model_config = ConfigDict(from_attributes=True)
    text: str


# ── Helper ────────────────────────────────────────────────────────

def _handle_result(result: dict):
    """將 Service 回傳結果轉換為 HTTP 回應或 HTTPException。

    BaseService.ok() 直接把 data 的 keys merge 進頂層 dict，
    BaseService.error() 有 error=True key。
    """
    if result.get("error"):
        status_code = result.get("status_code", 500)
        detail = result.get("message", "內部錯誤")
        raise HTTPException(status_code=status_code, detail=detail)
    # 移除 ok/message meta key，回傳業務欄位
    return {k: v for k, v in result.items() if k not in ("ok", "message")}


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/conversations", status_code=201)
def start_conversation(
    body: StartConversationRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """啟動 AI 蘇格拉底教練對話。

    - 404：節點不存在
    - 402：月配額不足（FREE=5次，PRO=20次）
    """
    svc = OrphanCoachService(db)
    result = svc.start_conversation(user_id=user_id, node_id=body.node_id)
    return _handle_result(result)


@router.post("/conversations/{conversation_id}/messages", status_code=200)
def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """向 AI 蘇格拉底教練發送回答。

    - 404：對話不存在
    - 403：非本人對話
    - 410：對話已超過 8 輪上限
    """
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=422, detail="訊息內容不可為空")
    svc = OrphanCoachService(db)
    result = svc.send_message(
        conversation_id=conversation_id,
        user_text=body.text.strip(),
        user_id=user_id,
    )
    return _handle_result(result)


@router.get("/conversations/{conversation_id}", status_code=200)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """取得蘇格拉底對話詳情（訊息清單、評分、mastery_committed、status）。

    - 404：對話不存在
    - 403：非本人對話
    """
    svc = OrphanCoachService(db)
    result = svc.get_conversation(conversation_id=conversation_id, user_id=user_id)
    return _handle_result(result)


@router.get("/conversations", status_code=200)
def find_active_conversation(
    node_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """查詢使用者對指定節點的進行中/暫停對話（C.4.4 接續用）。

    回傳 existing_conversation_id（str | null）。
    """
    svc = OrphanCoachService(db)
    result = svc.find_active_conversation(user_id=user_id, node_id=node_id)
    return _handle_result(result)


@router.post("/conversations/{conversation_id}/pause", status_code=200)
def pause_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """手動暫停對話（設置 paused_at 時間戳，之後可接續）。

    - 404：對話不存在
    - 403：非本人對話
    """
    svc = OrphanCoachService(db)
    result = svc.pause_conversation(conversation_id=conversation_id, user_id=user_id)
    return _handle_result(result)
