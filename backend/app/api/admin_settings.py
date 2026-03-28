"""平台管理後台 — 系統設定 API (super_admin only)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.admin_settings_service import AdminSettingsService

router = APIRouter(prefix="/admin/system-settings")


# ── System Maintenance ───────────────────────────────────────────────────────

@router.post("/reset-ai-limits")
def reset_ai_limits(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.reset_ai_limits(actor_id=user_id)
    return _handle_result(result)


@router.post("/clear-cache")
def clear_cache(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.clear_cache(actor_id=user_id)
    return _handle_result(result)


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


# ── AI Model Routing ──────────────────────────────────────────────────────────


@router.get("/model-routing")
def get_model_routing(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.get_model_routing(actor_id=user_id)
    return _handle_result(result)


class UpdateModelRoutingRequest(BaseModel):
    primary_model: str
    fallback_model: Optional[str] = None


@router.put("/model-routing/{plan}/{task_type}")
def update_model_routing(
    plan: str,
    task_type: str,
    body: UpdateModelRoutingRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.update_model_routing(
        actor_id=user_id,
        plan=plan,
        task_type=task_type,
        primary_model=body.primary_model,
        fallback_model=body.fallback_model,
    )
    return _handle_result(result)


# ── Plan Quota ────────────────────────────────────────────────────────────────


@router.get("/plan-quotas")
def get_plan_quotas(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.get_plan_quotas(actor_id=user_id)
    return _handle_result(result)


class UpdatePlanQuotaRequest(BaseModel):
    monthly_uploads: Optional[int] = None
    monthly_exams: Optional[int] = None
    daily_ai_chats: Optional[int] = None
    monthly_vision_pages: Optional[int] = None


@router.put("/plan-quota/{plan}")
def update_plan_quota(
    plan: str,
    body: UpdatePlanQuotaRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = service.update_plan_quota(actor_id=user_id, plan=plan, updates=updates)
    return _handle_result(result)


# ── System Announcements ──────────────────────────────────────────────────────


@router.get("/announcements")
def get_announcements(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.get_announcements(actor_id=user_id)
    return _handle_result(result)


class CreateAnnouncementRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = "info"
    display_mode: Optional[str] = "banner"
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None


@router.post("/announcements")
def create_announcement(
    body: CreateAnnouncementRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.create_announcement(actor_id=user_id, data=body.model_dump())
    return _handle_result(result)


@router.put("/announcements/{announcement_id}/deactivate")
def deactivate_announcement(
    announcement_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.deactivate_announcement(actor_id=user_id, announcement_id=announcement_id)
    return _handle_result(result)


@router.delete("/announcements/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.delete_announcement(actor_id=user_id, announcement_id=announcement_id)
    return _handle_result(result)


# ── Feature Flags ─────────────────────────────────────────────────────────────


@router.get("/feature-flags")
def get_feature_flags(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.get_feature_flags(actor_id=user_id)
    return _handle_result(result)


class UpdateFeatureFlagRequest(BaseModel):
    enabled: Optional[bool] = None
    rollout_percentage: Optional[int] = None
    target_plans: Optional[str] = None


@router.put("/feature-flags/{flag_id}")
def update_feature_flag(
    flag_id: str,
    body: UpdateFeatureFlagRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = service.update_feature_flag(actor_id=user_id, flag_id=flag_id, updates=updates)
    return _handle_result(result)


# ── Audit Logs ────────────────────────────────────────────────────────────────

@router.get("/audit-logs")
def get_audit_logs(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminSettingsService(db)
    result = service.get_audit_logs(actor_id=user_id)
    return _handle_result(result)
