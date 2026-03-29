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


@router.get("/dashboard/charts")
def get_dashboard_charts(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """管理後台圖表資料：用戶成長 + AI 成本分析。"""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func
    from app.models.user import User
    from app.models.exam import Exam, ExamStatus

    # User growth: last 6 months
    user_growth = []
    now = datetime.now(timezone.utc)
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_name = month_start.strftime("%m月")
        total_users = db.query(func.count(User.id)).filter(User.created_at <= month_start + timedelta(days=31)).scalar() or 0
        # Estimate DAU/MAU from exam activity
        exams_in_month = db.query(func.count(Exam.id)).filter(
            Exam.created_at >= month_start,
            Exam.created_at < month_start + timedelta(days=31),
        ).scalar() or 0
        user_growth.append({
            "name": month_name,
            "dau": max(1, exams_in_month // 30),
            "mau": max(1, min(total_users, exams_in_month * 3)),
        })

    # AI cost: estimated from exam generation count per month
    ai_cost = []
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_name = month_start.strftime("%m月")
        exams = db.query(func.count(Exam.id)).filter(
            Exam.created_at >= month_start,
            Exam.created_at < month_start + timedelta(days=31),
            Exam.status.in_([ExamStatus.READY, ExamStatus.SUBMITTED]),
        ).scalar() or 0
        # Estimate cost: ~$0.01 per exam for Gemini, ~$0.05 for Claude
        ai_cost.append({
            "name": month_name,
            "gemini": round(exams * 0.01, 2),
            "claude": round(exams * 0.003, 2),
            "gpt4": 0,
        })

    return {"user_growth": user_growth, "ai_cost": ai_cost}


@router.get("/dashboard/system-load")
def get_system_load(
    user_id: str = Depends(get_current_user_id),
):
    """系統負載（簡化版：估算值）。"""
    import os
    return {
        "cpu_percent": min(95, max(5, hash(str(os.getpid())) % 30 + 15)),
        "db_connections_percent": 25,
        "cache_hit_rate": 92,
    }


@router.get("/dashboard/alerts")
def get_dashboard_alerts(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """管理後台告警。"""
    from app.models.exam import Exam, ExamStatus
    from sqlalchemy import func

    failed_exams = db.query(func.count(Exam.id)).filter(Exam.status == ExamStatus.FAILED).scalar() or 0
    alerts = []
    if failed_exams > 0:
        alerts.append({"id": 1, "type": "warning", "message": f"{failed_exams} 個考試生成失敗", "time": "今天"})

    return {"alerts": alerts, "system_alerts": []}


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
    role: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.search_users(actor_id=user_id, keyword=keyword, plan=plan, role=role)
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
    start_date: Optional[str] = None
    end_date: Optional[str] = None


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
        start_date=body.start_date,
        end_date=body.end_date,
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


# ── Activate User ────────────────────────────────────────────────────────────

class ActivateUserRequest(BaseModel):
    target_user_id: Optional[str] = None


@router.post("/users/activate")
def activate_user(
    body: ActivateUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.activate_user(
        actor_id=user_id,
        target_user_id=body.target_user_id,
    )
    return _handle_result(result)


# ── Adjust Role ─────────────────────────────────────────────────────────────

class AdjustRoleRequest(BaseModel):
    target_user_id: Optional[str] = None
    target_email: Optional[str] = None
    role: str  # 'admin' or 'user'


@router.post("/users/adjust-role")
def adjust_role(
    body: AdjustRoleRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.adjust_role(
        actor_id=user_id,
        target_user_id=body.target_user_id,
        target_email=body.target_email,
        new_role=body.role,
    )
    return _handle_result(result)


# ── Delete User ─────────────────────────────────────────────────────────────

class DeleteUserRequest(BaseModel):
    target_user_id: str
    confirm_name: str


@router.post("/users/delete")
def delete_user(
    body: DeleteUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.delete_user(
        actor_id=user_id,
        target_user_id=body.target_user_id,
        confirm_name=body.confirm_name,
    )
    return _handle_result(result)


# ── Notify User ──────────────────────────────────────────────────────────────

class NotifyUserRequest(BaseModel):
    message: str


@router.post("/users/{target_user_id}/notify")
def notify_user(
    target_user_id: str,
    body: NotifyUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    result = service.notify_user(
        actor_id=user_id,
        target_user_id=target_user_id,
        message=body.message,
    )
    return _handle_result(result)
