"""平台管理後台 — 內容審核 API。"""

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.services.admin_moderation_service import AdminModerationService

router = APIRouter(prefix="/admin/moderation")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


# ── AI Abuse Monitoring ───────────────────────────────────────────────────────

@router.get("/ai-abuse")
def get_ai_abuse_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminModerationService(db)
    result = service.get_ai_abuse_dashboard(actor_id=user_id)
    return _handle_result(result)


@router.post("/ai-abuse/{target_user_id}/unlock")
def unlock_user_cooldown(
    target_user_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminModerationService(db)
    result = service.unlock_cooldown(actor_id=user_id, target_user_id=target_user_id)
    return _handle_result(result)


# ── Content Report Queue ──────────────────────────────────────────────────────

@router.get("/reports")
def get_report_queue(
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminModerationService(db)
    result = service.get_report_queue(actor_id=user_id, status=status)
    return _handle_result(result)


class ResolveReportRequest(BaseModel):
    action: str
    note: str


@router.post("/reports/{report_ref}/resolve")
def resolve_report(
    report_ref: str,
    body: ResolveReportRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminModerationService(db)
    result = service.resolve_report(
        actor_id=user_id,
        report_ref=report_ref,
        action=body.action,
        note=body.note,
    )
    return _handle_result(result)
