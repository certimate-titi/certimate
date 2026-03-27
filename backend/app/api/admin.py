"""平台管理後台 API。"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


# ── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.get_dashboard(user_id=user_id)
    return _handle_result(result)


@router.get("/settings")
def get_system_settings(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.get_system_settings(user_id=user_id)
    return _handle_result(result)


# ── User Management ──────────────────────────────────────────────────────────

@router.get("/users")
def search_users(
    keyword: Optional[str] = None,
    plan: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.search_users(actor_id=user_id, keyword=keyword, plan=plan)
    return _handle_result(result)


@router.get("/users/export")
def export_users_csv(
    plan: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.export_users_csv(actor_id=user_id, plan=plan)
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    csv_content = result["csv_content"]
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


@router.get("/users/{target_user_id}")
def get_user_detail(
    target_user_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.get_user_detail(actor_id=user_id, target_user_key=target_user_id)
    return _handle_result(result)


# ── Subscription Adjustment ──────────────────────────────────────────────────

class AdjustSubscriptionRequest(BaseModel):
    plan: str
    otp: str


@router.post("/users/{target_user_id}/adjust-subscription")
def adjust_subscription(
    target_user_id: str,
    body: AdjustSubscriptionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.adjust_subscription(
        actor_id=user_id,
        target_user_id=target_user_id,
        new_plan=body.plan,
        otp=body.otp,
    )
    return _handle_result(result)


# ── Suspend User ─────────────────────────────────────────────────────────────

class SuspendUserRequest(BaseModel):
    target_user_id: Optional[str] = None
    reason: Optional[str] = None


@router.post("/users/suspend")
def suspend_user(
    body: SuspendUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.suspend_user(
        actor_id=user_id,
        target_user_id=body.target_user_id,
        reason=body.reason,
    )
    return _handle_result(result)
