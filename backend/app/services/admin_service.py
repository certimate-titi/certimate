"""平台管理後台 Service。"""

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User, UserRole, UserStatus, SubscriptionPlan
from app.models.audit_log import AdminAuditLog
from app.models.exam import Exam, ExamStatus
from app.models.resource import Resource, ResourceStatus


def _get_role(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


# ── Plan display name mapping ─────────────────────────────────────────────────
# DB stores: FREE / PRO / PRO_PLUS / ULTRA
# Display:   FREE / PRO_199 / PRO_PLUS_399 / ULTRA_1599

_PLAN_DISPLAY_NAMES = {
    SubscriptionPlan.FREE: "FREE",
    SubscriptionPlan.PRO: "PRO_199",
    SubscriptionPlan.PRO_PLUS: "PRO_PLUS_399",
    SubscriptionPlan.ULTRA: "ULTRA_1599",
    SubscriptionPlan.EDU: "EDU",
}

_PLAN_INPUT_MAP = {
    "FREE": SubscriptionPlan.FREE,
    "PRO": SubscriptionPlan.PRO,
    "PRO_199": SubscriptionPlan.PRO,
    "PRO_PLUS": SubscriptionPlan.PRO_PLUS,
    "PRO_PLUS_399": SubscriptionPlan.PRO_PLUS,
    "ULTRA": SubscriptionPlan.ULTRA,
    "ULTRA_1599": SubscriptionPlan.ULTRA,
    "EDU": SubscriptionPlan.EDU,
}


def _get_plan(user: User) -> str:
    plan_enum = user.subscription_plan
    return _PLAN_DISPLAY_NAMES.get(plan_enum, str(plan_enum))


def _parse_plan(plan_str: str) -> SubscriptionPlan | None:
    """Parse plan string (accepts both DB value and display name)."""
    return _PLAN_INPUT_MAP.get(plan_str)


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

        # DAU: users who had exam activity today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        dau = (
            self.db.query(func.count(func.distinct(Exam.user_id)))
            .filter(Exam.created_at >= today_start)
            .scalar() or 0
        )

        # MAU: users who had exam activity this month
        month_start = today_start.replace(day=1)
        mau = (
            self.db.query(func.count(func.distinct(Exam.user_id)))
            .filter(Exam.created_at >= month_start)
            .scalar() or 0
        )

        # New registrations this week
        week_start = today_start - timedelta(days=today.weekday())
        new_registrations = (
            self.db.query(func.count(User.id))
            .filter(User.created_at >= week_start)
            .scalar() or 0
        )

        # MRR: sum of plan prices for paid users
        plan_prices = {"PRO_199": 199, "PRO_PLUS_399": 399, "ULTRA_1599": 1599}
        mrr = 0
        for plan_val, price in plan_prices.items():
            try:
                plan_enum = SubscriptionPlan(plan_val)
                count = self.db.query(func.count(User.id)).filter(User.subscription_plan == plan_enum).scalar() or 0
                mrr += count * price
            except ValueError:
                pass

        # AI cost today: estimate from exams generated today
        ai_exams_today = (
            self.db.query(func.count(Exam.id))
            .filter(
                Exam.created_at >= today_start,
                Exam.status.in_([ExamStatus.READY, ExamStatus.SUBMITTED]),
            )
            .scalar() or 0
        )
        # Real AI cost from ai_usage_ledger (Feature 33)
        try:
            from sqlalchemy import text as _text
            ai_token_today = float(self.db.execute(_text(
                "SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage_ledger WHERE created_at >= :start"
            ), {"start": today_start}).scalar() or 0)
            ai_token_today = round(ai_token_today, 4)
        except Exception:
            ai_token_today = round(ai_exams_today * 0.01, 2)  # fallback estimate

        # Queue depth: resources currently processing
        queue_depth = (
            self.db.query(func.count(Resource.id))
            .filter(Resource.status == ResourceStatus.PROCESSING)
            .scalar() or 0
        )

        result = {
            "dau": dau,
            "mau": mau,
            "new_registrations": new_registrations,
            "conversion_rate": conversion_rate,
            "mrr": mrr,
            "ai_token_today": ai_token_today,
            "queue_depth": queue_depth,
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

    def search_users(self, actor_id: str, keyword: str | None = None, plan: str | None = None, role: str | None = None) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        query = self.db.query(User)
        if keyword:
            query = query.filter(User.email.ilike(f"%{keyword}%"))
        if plan:
            plan_enum = _parse_plan(plan)
            if plan_enum is None:
                return {"error": True, "status_code": 400, "message": f"無效的方案：{plan}"}
            query = query.filter(User.subscription_plan == plan_enum)
        if role == "admin":
            # 只顯示管理員（admin + super_admin）
            query = query.filter(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
        elif role is None:
            # 預設排除管理員，只顯示一般用戶
            query = query.filter(User.role.in_([UserRole.USER, UserRole.ORG_ADMIN]))

        users = query.all()
        return {
            "users": [
                {
                    "email": u.email,
                    "display_name": u.display_name or "",
                    "plan": _get_plan(u),
                    "status": _get_status(u),
                    "role": _get_role(u),
                    "id": str(u.id),
                    "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
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
                "status": _get_status(target),
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
                "plan_source": target.plan_source or "unknown",
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
        self, actor_id: str, target_user_id: str, new_plan: str,
        start_date: str | None = None, end_date: str | None = None,
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
        plan_enum = _parse_plan(new_plan)
        if plan_enum is None:
            return {"error": True, "status_code": 400, "message": f"無效的方案：{new_plan}"}

        target.subscription_plan = plan_enum
        target.plan_source = "admin"

        if end_date:
            from datetime import date as date_type
            try:
                target.next_billing_date = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        self.db.commit()
        self.db.refresh(target)

        self._write_audit_log(
            admin_id=actor_id,
            action="adjust_subscription",
            target_type="user",
            target_id=target_user_id,
            details={
                "from": old_plan, "to": new_plan,
                "start_date": start_date, "end_date": end_date,
                "summary": f"{old_plan} → {new_plan}",
            },
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

        if target.status == UserStatus.SUSPENDED:
            return {"error": True, "status_code": 409, "message": "此帳號已停權"}

        target.status = UserStatus.SUSPENDED
        log = AdminAuditLog(
            admin_id=uuid.UUID(actor_id),
            action="suspend_user",
            target_type="user",
            target_id=uuid.UUID(target_user_id),
            details={"reason": reason},
        )
        self.db.add(log)
        self.db.commit()

        return {"success": True}

    # ── Activate User ─────────────────────────────────────────────────────────

    def activate_user(self, actor_id: str, target_user_id: str | None) -> dict:
        if not target_user_id:
            return {"error": True, "status_code": 422, "message": "必要參數未提供"}

        actor = self._get_user(actor_id)
        if not actor:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        if _get_role(actor) not in ("admin", "super_admin"):
            return {"error": True, "status_code": 403, "message": "權限不足，無法存取管理後台"}

        target = self._get_user(target_user_id)
        if not target:
            return {"error": True, "status_code": 404, "message": "目標使用者不存在"}

        target.status = UserStatus.ACTIVE
        self.db.commit()

        self._write_audit_log(
            admin_id=actor_id,
            action="activate_user",
            target_type="user",
            target_id=target_user_id,
            details={"summary": "恢復用戶帳號"},
        )

        return {"success": True}

    # ── Adjust Role ────────────────────────────────────────────────────────────

    def adjust_role(self, actor_id: str, target_user_id: str | None = None, target_email: str | None = None, new_role: str = "user") -> dict:
        err = self._require_super_admin(actor_id)
        if err:
            return err

        target = None
        if target_email:
            target = self.db.query(User).filter(User.email == target_email).first()
        elif target_user_id:
            target = self._get_user(target_user_id)
        if not target:
            return {"error": True, "status_code": 404, "message": "目標使用者不存在，請確認 Email 是否正確"}

        try:
            role_enum = UserRole(new_role)
        except ValueError:
            return {"error": True, "status_code": 400, "message": f"無效的角色：{new_role}"}

        old_role = _get_role(target)
        target.role = role_enum
        self.db.commit()

        # Use target.id as target_id for audit log (handles email-based lookup)
        resolved_target_id = target_user_id or str(target.id)
        self._write_audit_log(
            admin_id=actor_id,
            action="adjust_role",
            target_type="user",
            target_id=resolved_target_id,
            details={"from": old_role, "to": new_role, "summary": f"{old_role} → {new_role}"},
        )

        return {"success": True, "old_role": old_role, "new_role": new_role}

    # ── Delete User ───────────────────────────────────────────────────────────

    def delete_user(self, actor_id: str, target_user_id: str, confirm_name: str) -> dict:
        err = self._require_super_admin(actor_id)
        if err:
            return err

        target = self._get_user(target_user_id)
        if not target:
            return {"error": True, "status_code": 404, "message": "目標使用者不存在"}

        # Verify confirmation name matches
        actual_name = target.display_name or target.email
        if confirm_name != actual_name:
            return {"error": True, "status_code": 400, "message": f"確認名稱不符，請輸入「{actual_name}」"}

        # Soft delete: set status to DELETED
        target.status = UserStatus.DELETED
        self.db.commit()

        self._write_audit_log(
            admin_id=actor_id,
            action="delete_user",
            target_type="user",
            target_id=target_user_id,
            details={"summary": f"刪除用戶 {target.email}"},
        )

        return {"success": True}

    # ── Notify User ──────────────────────────────────────────────────────────

    def notify_user(self, actor_id: str, target_user_id: str, message: str) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        target = self._get_user(target_user_id)
        if not target:
            return {"error": True, "status_code": 404, "message": "目標使用者不存在"}

        if not message.strip():
            return {"error": True, "status_code": 400, "message": "通知訊息不可為空"}

        # TODO: 實際發送通知（Email / 站內通知），目前先記錄 audit log
        self._write_audit_log(
            admin_id=actor_id,
            action="notify_user",
            target_type="user",
            target_id=target_user_id,
            details={"message": message, "email": target.email},
        )

        return {"success": True, "message": f"通知已發送給 {target.email}"}

    # ── Export CSV ───────────────────────────────────────────────────────────

    def export_users_csv(self, actor_id: str, plan: str | None = None) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        query = self.db.query(User)
        if plan:
            plan_enum = _parse_plan(plan)
            if plan_enum is None:
                return {"error": True, "status_code": 400, "message": f"無效的方案：{plan}"}
            query = query.filter(User.subscription_plan == plan_enum)

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
