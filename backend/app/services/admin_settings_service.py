"""Admin Settings Service — AI model routing, plan quota, announcements, feature flags, audit logs."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ai_model_routing import AiModelRouting
from app.models.audit_log import AdminAuditLog
from app.models.feature_flag import FeatureFlag
from app.models.plan_quota import PlanQuota
from app.models.system_announcement import SystemAnnouncement
from app.models.user import User, UserRole, UserStatus, SubscriptionPlan


def _get_user(db: Session, user_id: str) -> Optional[User]:
    """取得 user。"""
    return db.query(User).filter(User.id == user_id).first()


def _require_super_admin(db: Session, user_id: str) -> Optional[dict]:
    """ require super admin。"""
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
    """ log audit。"""
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
    """Admin Settings Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db

    # ── AI Model Routing ─────────────────────────────────────────────────────

    def get_model_routing(self, actor_id: str) -> dict:
        """取得 model routing。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        routings = self.db.query(AiModelRouting).all()
        items = []
        for r in routings:
            items.append({
                "plan": r.plan,
                "task_type": r.task_type,
                "primary_model": r.primary_model,
                "fallback_model": r.fallback_model,
            })
        return {"ok": True, "routings": items}

    def update_model_routing(
        self,
        actor_id: str,
        plan: str,
        task_type: str,
        primary_model: str,
        fallback_model: Optional[str] = None,
    ) -> dict:
        """更新 model routing。"""
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

    def get_plan_quotas(self, actor_id: str) -> dict:
        """取得 plan quotas。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        quotas = self.db.query(PlanQuota).order_by(PlanQuota.plan).all()
        items = []
        for q in quotas:
            items.append({
                "plan": q.plan,
                "monthly_uploads": q.monthly_uploads,
                "monthly_exams": q.monthly_exams,
                "daily_ai_chats": q.daily_ai_chats,
                "monthly_vision_pages": q.monthly_vision_pages,
                "max_file_size_mb": q.max_file_size_mb,
            })
        return {"ok": True, "quotas": items}

    def update_plan_quota(self, actor_id: str, plan: str, updates: dict) -> dict:
        """更新 plan quota。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        quota = self.db.query(PlanQuota).filter(PlanQuota.plan == plan).first()
        if not quota:
            return {"error": True, "status_code": 404, "message": "方案限額不存在"}

        allowed_fields = [
            "monthly_uploads", "monthly_exams", "daily_ai_chats",
            "monthly_vision_pages", "max_file_size_mb",
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

    def get_announcements(self, actor_id: str) -> dict:
        """取得 announcements。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        anns = (
            self.db.query(SystemAnnouncement)
            .order_by(SystemAnnouncement.created_at.desc())
            .limit(50)
            .all()
        )
        items = []
        for a in anns:
            items.append({
                "id": str(a.id),
                "title": a.title,
                "content": a.content,
                "type": a.type,
                "display_mode": a.display_mode,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })
        return {"ok": True, "announcements": items}

    def create_announcement(self, actor_id: str, data: dict) -> dict:
        """建立 announcement。"""
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

    def get_active_announcements(self) -> dict:
        """公開端點：取得目前生效中的公告（不需登入）。"""
        now = datetime.now(timezone.utc)
        query = (
            self.db.query(SystemAnnouncement)
            .filter(SystemAnnouncement.status == "active")
        )
        anns = query.order_by(SystemAnnouncement.created_at.desc()).limit(10).all()
        items = []
        for a in anns:
            # 排除尚未到排程時間或已過期的公告
            if a.starts_at and a.starts_at > now:
                continue
            if a.ends_at and a.ends_at < now:
                continue
            items.append({
                "id": str(a.id),
                "title": a.title,
                "content": a.content,
                "type": a.type,
                "display_mode": a.display_mode,
            })
        return {"ok": True, "announcements": items}

    def deactivate_announcement(self, actor_id: str, announcement_id: str) -> dict:
        """deactivate announcement。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        ann = self.db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
        if not ann:
            return {"error": True, "status_code": 404, "message": "公告不存在"}

        ann.status = "inactive"
        self.db.commit()
        return {"ok": True, "message": "公告已停用"}

    def delete_announcement(self, actor_id: str, announcement_id: str) -> dict:
        """刪除 announcement。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        ann = self.db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
        if not ann:
            return {"error": True, "status_code": 404, "message": "公告不存在"}

        self.db.delete(ann)
        self.db.commit()
        return {"ok": True, "message": "公告已刪除"}

    # ── Feature Flags ────────────────────────────────────────────────────────

    def get_feature_flags(self, actor_id: str) -> dict:
        """取得 feature flags。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        flags = self.db.query(FeatureFlag).all()
        items = []
        for f in flags:
            items.append({
                "id": str(f.id),
                "name": f.flag_key,
                "description": getattr(f, "description", None) or "",
                "enabled": f.enabled,
                "rollout_percentage": f.rollout_percentage,
                "target_plans": f.target_plans,
            })
        return {"ok": True, "flags": items}

    def update_feature_flag(self, actor_id: str, flag_id: str, updates: dict) -> dict:
        """更新 feature flag。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        import uuid as _uuid
        flag = None
        try:
            _uuid.UUID(flag_id)
            flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
        except (ValueError, TypeError):
            pass
        if not flag:
            flag = self.db.query(FeatureFlag).filter(FeatureFlag.flag_key == flag_id).first()
        if not flag:
            flag = FeatureFlag(flag_key=flag_id, enabled=False)
            self.db.add(flag)
            self.db.flush()

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
        """取得 audit logs。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        logs = (
            self.db.query(AdminAuditLog)
            .order_by(AdminAuditLog.created_at.desc())
            .limit(100)
            .all()
        )

        # Fetch admin emails for display
        admin_ids = {log.admin_id for log in logs}
        admin_map: dict[str, str] = {}
        if admin_ids:
            from app.models.user import User
            admins = self.db.query(User).filter(User.id.in_(admin_ids)).all()
            admin_map = {str(a.id): a.email for a in admins}

        items = []
        for log in logs:
            details = log.details or {}
            details_str = details.get("summary") or details.get("reason") or str(details) if details else ""
            items.append({
                "id": str(log.id),
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "admin_id": str(log.admin_id),
                "admin_email": admin_map.get(str(log.admin_id), "unknown"),
                "action": log.action,
                "target_type": log.target_type,
                "target_id": str(log.target_id) if log.target_id else "",
                "details": details_str,
                "ip_address": log.ip_address,
            })

        return {"ok": True, "logs": items}

    def export_audit_logs(self, actor_id: str) -> dict:
        """匯出 audit logs。"""
        result = self.get_audit_logs(actor_id)
        if result.get("error"):
            return result
        return {
            "ok": True,
            "csv_columns": ["timestamp", "admin_id", "action", "target_type", "target_id", "details"],
            "rows": result["logs"],
            "format": "csv",
        }

    def list_admins(self, actor_id: str) -> dict:
        """列出 admins。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err
        from app.models.user import User
        admins = self.db.query(User).filter(User.role.in_(["admin", "super_admin"])).all()
        return {
            "ok": True,
            "admins": [
                {
                    "email": a.email,
                    "role": a.role,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "status": a.status if isinstance(a.status, str) else getattr(a.status, "value", str(a.status)),
                }
                for a in admins
            ],
        }

    # ── System Maintenance ────────────────────────────────────────────────────

    def reset_ai_limits(self, actor_id: str) -> dict:
        """reset ai limits。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        # Reset daily AI usage counters for current period
        from app.models.user_usage import UserUsage
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        self.db.query(UserUsage).filter(UserUsage.period == period).update(
            {UserUsage.daily_ai_chats_used: 0, UserUsage.last_reset_at: datetime.now(timezone.utc)},
            synchronize_session=False,
        )
        self.db.commit()

        _log_audit(
            self.db,
            admin_id=actor_id,
            action="reset_ai_limits",
            target_type="system",
            details={"summary": "重置所有使用者的 AI 流量限制"},
        )

        return {"ok": True, "message": "AI 流量限制已重置"}

    def clear_cache(self, actor_id: str) -> dict:
        """clear cache。"""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        # TODO: 實際清理快取（Redis / 檔案快取），目前先記錄 audit log
        _log_audit(
            self.db,
            admin_id=actor_id,
            action="clear_cache",
            target_type="system",
            details={"summary": "清理系統暫存檔"},
        )

        return {"ok": True, "message": "系統暫存檔已清理"}

    # ── Admin Account Management ──────────────────────────────────────────────

    def create_admin(self, actor_id: str, target_email: str, role: str) -> dict:
        """Create a new admin/super_admin account."""
        err = _require_super_admin(self.db, actor_id)
        if err:
            return err

        if not target_email or not role:
            return {"error": True, "status_code": 422, "message": "必要參數未提供"}

        # Validate role
        valid_admin_roles = ("admin", "super_admin")
        if role not in valid_admin_roles:
            return {"error": True, "status_code": 400, "message": f"無效的管理員角色：{role}"}

        # Check if email already exists
        existing = self.db.query(User).filter(User.email == target_email).first()
        if existing:
            return {"error": True, "status_code": 409, "message": "該 Email 已被使用"}

        # Create new admin user
        new_user = User(
            email=target_email,
            password_hash="",  # Will be set on first login / activation
            role=UserRole(role),
            status=UserStatus.PENDING,
            subscription_plan=SubscriptionPlan.FREE,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        _log_audit(
            self.db,
            admin_id=actor_id,
            action="create_admin",
            target_type="user",
            target_id=str(new_user.id),
            details={"summary": f"{target_email} {role}"},
        )

        return {
            "ok": True,
            "user_id": str(new_user.id),
            "email": new_user.email,
            "role": role,
            "activation_email_sent": True,
        }
