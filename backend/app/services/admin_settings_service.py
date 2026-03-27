"""Admin Settings Service — AI model routing, plan quota, announcements, feature flags, audit logs."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ai_model_routing import AiModelRouting
from app.models.audit_log import AdminAuditLog
from app.models.feature_flag import FeatureFlag
from app.models.plan_quota import PlanQuota
from app.models.system_announcement import SystemAnnouncement
from app.models.user import User, UserRole


def _get_user(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def _require_super_admin(db: Session, user_id: str) -> Optional[dict]:
    user = _get_user(db, user_id)
    if not user:
        return {"error": True, "status_code": 401, "message": "未授權"}
    if user.role != UserRole.SUPER_ADMIN:
        return {"error": True, "status_code": 403, "message": "權限不足"}
    return None


def _log_audit(
    db: Session,
    admin_id: str,
    action: str,
    target_type: Optional[str] = None,
    target_id=None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
):
    log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()


class AdminSettingsService:
    def __init__(self, db: Session):
        self.db = db

    # ── AI Model Routing ─────────────────────────────────────────────────────

    def update_model_routing(
        self,
        actor_id: str,
        plan: str,
        task_type: str,
        primary_model: str,
        fallback_model: Optional[str] = None,
    ) -> dict:
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        routing = (
            self.db.query(AiModelRouting)
            .filter(AiModelRouting.plan == plan, AiModelRouting.task_type == task_type)
            .first()
        )
        if not routing:
            return {"error": True, "status_code": 404, "message": "路由設定不存在"}

        old_model = routing.primary_model
        routing.primary_model = primary_model
        if fallback_model is not None:
            routing.fallback_model = fallback_model
        self.db.commit()
        self.db.refresh(routing)

        _log_audit(
            self.db,
            admin_id=actor_id,
            action="update_model_routing",
            target_type="ai_model_routing",
            target_id=routing.id,
            details={"message": f"{plan} {task_type}: {old_model} → {primary_model}"},
        )

        return {"ok": True, "routing": {
            "plan": routing.plan,
            "task_type": routing.task_type,
            "primary_model": routing.primary_model,
            "fallback_model": routing.fallback_model,
        }}

    # ── Plan Quota ───────────────────────────────────────────────────────────

    def update_plan_quota(self, actor_id: str, plan: str, updates: dict) -> dict:
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        quota = self.db.query(PlanQuota).filter(PlanQuota.plan == plan).first()
        if not quota:
            return {"error": True, "status_code": 404, "message": "方案限額不存在"}

        allowed_fields = [
            "monthly_uploads", "monthly_exams", "daily_ai_chats", "monthly_vision_pages"
        ]
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(quota, field, value)

        quota.updated_by = actor_id
        self.db.commit()
        self.db.refresh(quota)

        return {"ok": True, "quota": {
            "plan": quota.plan,
            "monthly_uploads": quota.monthly_uploads,
            "monthly_exams": quota.monthly_exams,
            "daily_ai_chats": quota.daily_ai_chats,
            "monthly_vision_pages": quota.monthly_vision_pages,
        }}

    # ── System Announcements ─────────────────────────────────────────────────

    def create_announcement(self, actor_id: str, data: dict) -> dict:
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        title = data.get("title", "").strip()
        content = data.get("content", "").strip()

        if not title or not content:
            return {"error": True, "status_code": 400, "message": "必要參數未提供"}

        ann_type = data.get("type", "info")
        display_mode = data.get("display_mode", "banner")
        starts_at = None
        ends_at = None

        if data.get("starts_at"):
            starts_at = datetime.fromisoformat(data["starts_at"]).replace(tzinfo=timezone.utc)
        if data.get("ends_at"):
            ends_at = datetime.fromisoformat(data["ends_at"]).replace(tzinfo=timezone.utc)

        announcement = SystemAnnouncement(
            title=title,
            content=content,
            type=ann_type,
            display_mode=display_mode,
            status="active",
            starts_at=starts_at,
            ends_at=ends_at,
            created_by=actor_id,
        )
        self.db.add(announcement)
        self.db.commit()
        self.db.refresh(announcement)

        return {"ok": True, "announcement": {
            "id": str(announcement.id),
            "title": announcement.title,
            "content": announcement.content,
            "type": announcement.type,
            "status": announcement.status,
        }}

    # ── Feature Flags ────────────────────────────────────────────────────────

    def update_feature_flag(self, actor_id: str, flag_id: str, updates: dict) -> dict:
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
        if not flag:
            return {"error": True, "status_code": 404, "message": "Feature Flag 不存在"}

        if "enabled" in updates:
            flag.enabled = updates["enabled"]
        if "rollout_percentage" in updates:
            flag.rollout_percentage = updates["rollout_percentage"]
        if "target_plans" in updates:
            flag.target_plans = updates["target_plans"]

        self.db.commit()
        self.db.refresh(flag)

        return {"ok": True, "flag": {
            "id": str(flag.id),
            "flag_key": flag.flag_key,
            "enabled": flag.enabled,
            "rollout_percentage": flag.rollout_percentage,
            "target_plans": flag.target_plans,
        }}

    # ── Audit Logs ───────────────────────────────────────────────────────────

    def get_audit_logs(self, actor_id: str) -> dict:
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        logs = (
            self.db.query(AdminAuditLog)
            .order_by(AdminAuditLog.created_at.desc())
            .limit(100)
            .all()
        )

        items = []
        for log in logs:
            items.append({
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "admin_id": str(log.admin_id),
                "action": log.action,
                "target_type": log.target_type,
                "target_id": str(log.target_id) if log.target_id else None,
                "details": log.details,
                "ip_address": log.ip_address,
            })

        return {"ok": True, "logs": items}
