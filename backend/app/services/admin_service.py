"""平台管理後台 Service。"""

import csv
import io
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, UserStatus, SubscriptionPlan
from app.models.audit_log import AdminAuditLog


def _get_role(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _get_plan(user: User) -> str:
    return user.subscription_plan.value if hasattr(user.subscription_plan, "value") else str(user.subscription_plan)


def _get_status(user: User) -> str:
    return user.status.value if hasattr(user.status, "value") else str(user.status)


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def _get_user(self, user_id: str) -> User | None:
        return self.db.query(User).filter_by(id=uuid.UUID(user_id)).first()

    def _require_admin(self, user_id: str) -> dict | None:
        """Return error dict if not admin/super_admin, else None."""
        user = self._get_user(user_id)
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        role = _get_role(user)
        if role not in ("admin", "super_admin"):
            return {"error": True, "status_code": 403, "message": "權限不足，無法存取管理後台"}
        return None

    def _require_super_admin(self, user_id: str) -> dict | None:
        user = self._get_user(user_id)
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        role = _get_role(user)
        if role != "super_admin":
            return {"error": True, "status_code": 403, "message": "權限不足，僅 super_admin 可存取系統設定"}
        return None

    def _write_audit_log(
        self,
        admin_id: str,
        action: str,
        target_type: str | None = None,
        target_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        log = AdminAuditLog(
            admin_id=uuid.UUID(admin_id),
            action=action,
            target_type=target_type,
            target_id=uuid.UUID(target_id) if target_id else None,
            details=details,
        )
        self.db.add(log)
        self.db.commit()

    # ── Dashboard ────────────────────────────────────────────────────────────

    def get_dashboard(self, user_id: str) -> dict:
        err = self._require_admin(user_id)
        if err:
            return err

        actor = self._get_user(user_id)
        role = _get_role(actor)

        today = datetime.now(timezone.utc).date()
        total = self.db.query(User).count()
        paid = (
            self.db.query(User)
            .filter(User.subscription_plan != SubscriptionPlan.FREE)
            .count()
        )
        conversion_rate = round(paid / total, 4) if total > 0 else 0.0

        result = {
            "dau": 0,
            "mau": 0,
            "new_registrations": 0,
            "conversion_rate": conversion_rate,
            "mrr": 0,
            "ai_token_today": 0,
            "queue_depth": 0,
        }

        if role == "admin":
            result["can_access_settings"] = False

        return result

    def get_system_settings(self, user_id: str) -> dict:
        err = self._require_super_admin(user_id)
        if err:
            return err
        return {"settings": {}}

    # ── User Search ──────────────────────────────────────────────────────────

    def search_users(self, actor_id: str, keyword: str | None = None, plan: str | None = None) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        query = self.db.query(User)
        if keyword:
            query = query.filter(User.email.ilike(f"%{keyword}%"))
        if plan:
            try:
                plan_enum = SubscriptionPlan(plan)
                query = query.filter(User.subscription_plan == plan_enum)
            except ValueError:
                return {"error": True, "status_code": 400, "message": f"無效的方案：{plan}"}

        users = query.all()
        return {
            "users": [
                {
                    "email": u.email,
                    "plan": _get_plan(u),
                    "status": _get_status(u),
                    "role": _get_role(u),
                    "id": str(u.id),
                }
                for u in users
            ]
        }

    # ── User Detail ──────────────────────────────────────────────────────────

    def get_user_detail(self, actor_id: str, target_user_key: str) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        # target_user_key could be numeric shorthand stored in context.ids
        # The API receives actual UUID from the client
        target = self._get_user(target_user_key)
        if not target:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        return {
            "profile": {
                "display_name": target.display_name,
                "email": target.email,
                "role": _get_role(target),
                "created_at": target.created_at.isoformat() if target.created_at else None,
            },
            "subscription": {
                "plan": _get_plan(target),
                "status": (
                    target.subscription_status.value
                    if hasattr(target.subscription_status, "value")
                    else str(target.subscription_status)
                ),
                "next_billing_date": (
                    target.next_billing_date.isoformat() if target.next_billing_date else None
                ),
            },
            "behavior": {
                "last_login_at": target.last_login_at.isoformat() if target.last_login_at else None,
                "total_login_count": 0,
                "last_exam_date": None,
            },
            "token_usage": {
                "monthly_tokens": 0,
                "remaining_quota": 0,
            },
            "login_history": [],
            "anomalies": {
                "cooling_records": [],
                "anomaly_records": [],
            },
        }

    # ── Adjust Subscription ──────────────────────────────────────────────────

    def adjust_subscription(
        self, actor_id: str, target_user_id: str, new_plan: str, otp: str
    ) -> dict:
        actor = self._get_user(actor_id)
        if not actor:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        if _get_role(actor) != "super_admin":
            return {"error": True, "status_code": 403, "message": "權限不足，僅 super_admin 可調整訂閱"}

        target = self._get_user(target_user_id)
        if not target:
            return {"error": True, "status_code": 404, "message": "目標使用者不存在"}

        old_plan = _get_plan(target)
        try:
            plan_enum = SubscriptionPlan(new_plan)
        except ValueError:
            return {"error": True, "status_code": 400, "message": f"無效的方案：{new_plan}"}

        target.subscription_plan = plan_enum
        self.db.commit()
        self.db.refresh(target)

        self._write_audit_log(
            admin_id=actor_id,
            action="adjust_subscription",
            target_type="user",
            target_id=target_user_id,
            details={"from": old_plan, "to": new_plan, "summary": f"{old_plan} → {new_plan}"},
        )

        return {"success": True, "old_plan": old_plan, "new_plan": new_plan}

    # ── Suspend User ─────────────────────────────────────────────────────────

    def suspend_user(self, actor_id: str, target_user_id: str | None, reason: str | None) -> dict:
        if not target_user_id:
            return {"error": True, "status_code": 422, "message": "必要參數未提供"}
        if not reason:
            return {"error": True, "status_code": 422, "message": "必要參數未提供"}

        actor = self._get_user(actor_id)
        if not actor:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        if _get_role(actor) not in ("admin", "super_admin"):
            return {"error": True, "status_code": 403, "message": "權限不足，無法存取管理後台"}

        target = self._get_user(target_user_id)
        if not target:
            return {"error": True, "status_code": 404, "message": "目標使用者不存在"}

        target.status = UserStatus.SUSPENDED
        self.db.commit()

        self._write_audit_log(
            admin_id=actor_id,
            action="suspend_user",
            target_type="user",
            target_id=target_user_id,
            details={"reason": reason},
        )

        return {"success": True}

    # ── Export CSV ───────────────────────────────────────────────────────────

    def export_users_csv(self, actor_id: str, plan: str | None = None) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        query = self.db.query(User)
        if plan:
            try:
                plan_enum = SubscriptionPlan(plan)
                query = query.filter(User.subscription_plan == plan_enum)
            except ValueError:
                return {"error": True, "status_code": 400, "message": f"無效的方案：{plan}"}

        users = query.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["email", "display_name", "plan", "status", "created_at"])
        for u in users:
            writer.writerow([
                u.email,
                u.display_name or "",
                _get_plan(u),
                _get_status(u),
                u.created_at.isoformat() if u.created_at else "",
            ])

        return {"csv_content": output.getvalue()}
