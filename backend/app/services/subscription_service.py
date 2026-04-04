"""訂閱管理 Service。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User, SubscriptionPlan, SubscriptionStatus
from app.models.invoice import Invoice
from app.models.plan_quota import PlanQuota

PLAN_ORDER = ["FREE", "PRO", "PRO_PLUS", "ULTRA"]
PLAN_FEES = {"FREE": 0, "PRO": 199, "PRO_PLUS": 399, "ULTRA": 1599, "EDU": 0}

# API display name -> DB enum value
PLAN_DISPLAY_TO_DB = {
    "FREE": "FREE",
    "PRO_199": "PRO",
    "PRO_PLUS_399": "PRO_PLUS",
    "ULTRA_1599": "ULTRA",
    "EDU": "EDU",
    # Also accept DB values directly
    "PRO": "PRO",
    "PRO_PLUS": "PRO_PLUS",
    "ULTRA": "ULTRA",
}

# DB enum value -> API display name
PLAN_DB_TO_DISPLAY = {
    "FREE": "FREE",
    "PRO": "PRO_199",
    "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599",
    "EDU": "EDU",
}

# Default plan comparison table
PLAN_COMPARISON = [
    {"plan": "FREE", "daily_ai_chats": 3, "monthly_uploads": 5, "monthly_exams": 10, "monthly_vision_pages": 0, "self_question": True, "advanced_coach": False},
    {"plan": "PRO_199", "daily_ai_chats": 30, "monthly_uploads": 50, "monthly_exams": 100, "monthly_vision_pages": 0, "self_question": True, "advanced_coach": False},
    {"plan": "PRO_PLUS_399", "daily_ai_chats": 200, "monthly_uploads": 200, "monthly_exams": 500, "monthly_vision_pages": 50, "self_question": True, "advanced_coach": True},
    {"plan": "ULTRA_1599", "daily_ai_chats": "unlimited", "monthly_uploads": "unlimited", "monthly_exams": "unlimited", "monthly_vision_pages": 500, "self_question": True, "advanced_coach": True},
    {"plan": "EDU", "daily_ai_chats": 5, "monthly_uploads": 0, "monthly_exams": "unlimited", "monthly_vision_pages": 0, "self_question": False, "advanced_coach": False},
]

# Plans that include advanced coach
PLANS_WITH_COACH = {"PRO_PLUS", "ULTRA"}
COACH_QUOTA = {"PRO_PLUS": 200, "ULTRA": "unlimited"}


def _resolve_plan(plan_display: str) -> str:
    """Convert API display name to DB enum value."""
    return PLAN_DISPLAY_TO_DB.get(plan_display, plan_display)


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def subscribe(self, user_id: str, plan: str):
        """訂閱方案。"""
        if not plan or not plan.strip():
            return {"error": True, "status_code": 400, "message": "必要參數未提供"}

        if plan == "EDU":
            return {"error": True, "status_code": 400, "message": "EDU 方案僅限機構管理員指派，無法自行訂閱"}

        db_plan = _resolve_plan(plan)

        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        current_plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        current_status = user.subscription_status.value if hasattr(user.subscription_status, 'value') else str(user.subscription_status)

        # Cancelled user trying to re-subscribe same plan before expiry
        if current_status == "cancelled" and current_plan == db_plan:
            return {"error": True, "status_code": 400, "message": f"您的 {plan} 方案尚未到期，請等待到期後再訂閱"}

        # Active user trying to subscribe same plan
        if current_plan == db_plan and current_status == "active":
            return {"error": True, "status_code": 400, "message": "您已訂閱此方案"}

        return {"message": "訂閱成功"}

    def get_subscription_info(self, user_id: str):
        """查看訂閱資訊。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan_db = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        plan_display = PLAN_DB_TO_DISPLAY.get(plan_db, plan_db)
        fee = PLAN_FEES.get(plan_db, 0)
        sub_status = user.subscription_status.value if hasattr(user.subscription_status, 'value') else str(user.subscription_status)

        result = {
            "current_plan": plan_display,
            "monthly_fee": fee,
            "subscription_status": sub_status,
        }

        if user.next_billing_date:
            result["next_billing"] = user.next_billing_date.strftime("%Y-%m-%d")
        else:
            result["next_billing"] = None

        # Coach remaining quota
        if plan_db in PLANS_WITH_COACH:
            result["coach_remaining_quota"] = COACH_QUOTA.get(plan_db, 0)

        # Trial info
        if sub_status == "trial":
            now = datetime.now(timezone.utc)
            if user.trial_end_date:
                remaining = (user.trial_end_date - now).days
                remaining = max(0, remaining)
                result["trial_days_left"] = remaining

        # Plan comparison
        result["plan_comparison"] = PLAN_COMPARISON

        return result

    def upgrade(self, user_id: str, plan: str):
        """升級方案（完成付款）。"""
        db_plan = _resolve_plan(plan)

        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan_enum = SubscriptionPlan(db_plan)
        user.subscription_plan = plan_enum
        user.subscription_status = SubscriptionStatus.ACTIVE
        self.db.commit()

        result = {"message": f"已升級至 {plan} 方案"}

        # Include coach quota for plans with advanced coach
        if db_plan in PLANS_WITH_COACH:
            quota_val = COACH_QUOTA.get(db_plan, 0)
            result["remaining_quota"] = quota_val
            result["coach_quota_remaining"] = quota_val

        return result

    def downgrade(self, user_id: str, plan: str):
        """降級方案（下期生效）。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        effective_date = user.next_billing_date.strftime("%Y-%m-%d") if user.next_billing_date else "下一計費週期"

        return {
            "downgrade_effective": effective_date,
            "message": "降級將於下一計費週期生效",
        }

    def cancel(self, user_id: str):
        """取消訂閱。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        user.subscription_status = SubscriptionStatus.CANCELLED
        self.db.commit()

        return {"message": "訂閱已取消"}

    def get_invoices(self, user_id: str):
        """查看帳單紀錄。"""
        user_uuid = uuid.UUID(user_id)

        invoices = (
            self.db.query(Invoice)
            .filter_by(user_id=user_uuid)
            .order_by(Invoice.created_at.desc())
            .all()
        )

        items = []
        for inv in invoices:
            items.append({
                "invoice_id": inv.stripe_invoice_id or str(inv.id),
                "amount": float(inv.amount),
                "plan": inv.plan,
                "status": inv.status,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
            })

        return {"invoices": items}
