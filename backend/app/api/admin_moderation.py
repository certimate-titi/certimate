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


# ── Frontend-compatible endpoints ────────────────────────────────────────────

@router.get("/queue")
def get_moderation_queue(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """審核佇列（映射到 reports API）。"""
    service = AdminModerationService(db)
    result = service.get_report_queue(actor_id=user_id, status="pending")
    if result.get("error"):
        return _handle_result(result)
    # Transform to frontend expected format
    items = []
    for r in result.get("reports", []):
        items.append({
            "id": r.get("id", ""),
            "user": r.get("reporter_email", "unknown"),
            "type": r.get("content_type", "content"),
            "content": r.get("reason", "")[:50],
            "reason": r.get("reason", ""),
            "status": r.get("status", "pending"),
            "time": r.get("created_at", ""),
        })
    return {"items": items}


@router.get("/stats")
def get_moderation_stats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """審核統計。"""
    service = AdminModerationService(db)
    abuse = service.get_ai_abuse_dashboard(actor_id=user_id)
    reports = service.get_report_queue(actor_id=user_id)
    pending = len([r for r in reports.get("reports", []) if r.get("status") == "pending"])
    cooled = len(abuse.get("cooled_users", []))
    # Auto-flagged: count FUP soft cap triggers from audit log today
    from sqlalchemy import func, text as _text
    auto_flagged = 0
    try:
        auto_flagged = db.execute(_text(
            "SELECT count(*) FROM admin_audit_logs WHERE action='fup_soft_cap_triggered' AND created_at >= CURRENT_DATE"
        )).scalar() or 0
    except Exception:
        pass

    # False positive rate: resolved reports marked as 'false_positive' / total resolved
    total_resolved = 0
    false_positives = 0
    try:
        from app.models.content_report import ContentReport
        total_resolved = db.query(func.count(ContentReport.id)).filter(
            ContentReport.status != 'pending'
        ).scalar() or 0
        false_positives = db.query(func.count(ContentReport.id)).filter(
            ContentReport.status == 'false_positive'
        ).scalar() or 0
    except Exception:
        pass
    fp_rate = f"{round(false_positives * 100 / total_resolved)}%" if total_resolved > 0 else "N/A"

    return {
        "pending_reports": pending,
        "auto_flagged_today": auto_flagged,
        "cooled_users": cooled,
        "false_positive_rate": fp_rate,
    }


@router.get("/abuse")
def get_abuse_monitoring(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """濫用監控（映射到 ai-abuse API）。"""
    service = AdminModerationService(db)
    result = service.get_ai_abuse_dashboard(actor_id=user_id)
    if result.get("error"):
        return _handle_result(result)
    items = []
    for u in result.get("cooling_users", []):
        items.append({
            "id": u.get("user_id", ""),
            "user": u.get("email", "unknown"),
            "metric": u.get("reason") or "AI 超綱提問",
            "count": str(u.get("remaining_seconds", 0)),
            "status": "cooling",
            "time": u.get("cooldown_until", ""),
        })
    return {"items": items}


@router.post("/{item_id}/approve")
def approve_item(
    item_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """通過審核項目。"""
    service = AdminModerationService(db)
    result = service.resolve_report(
        actor_id=user_id,
        report_ref=item_id,
        action="approve",
        note="approved via moderation panel",
    )
    return _handle_result(result)


@router.post("/{item_id}/reject")
def reject_item(
    item_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """拒絕/移除審核項目。"""
    service = AdminModerationService(db)
    result = service.resolve_report(
        actor_id=user_id,
        report_ref=item_id,
        action="reject",
        note="rejected via moderation panel",
    )
    return _handle_result(result)


@router.get("/content-review")
def get_content_review_queue(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """內容審核佇列。"""
    service = AdminModerationService(db)
    result = service.get_report_queue(actor_id=user_id)
    if result.get("error"):
        return _handle_result(result)
    items = []
    for i, r in enumerate(result.get("reports", [])):
        items.append({
            "id": i + 1,
            "type": r.get("content_type", "resource"),
            "content": r.get("reason", ""),
            "reporter": r.get("reporter_email", ""),
            "status": r.get("status", "pending"),
            "date": r.get("created_at", ""),
        })
    return {"items": items}
