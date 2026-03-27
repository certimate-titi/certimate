"""訂閱管理 Service。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User, SubscriptionPlan, SubscriptionStatus
from app.models.invoice import Invoice

PLAN_ORDER = ["FREE", "PRO", "PRO_PLUS", "ULTRA"]
PLAN_FEES = {"FREE": 0, "PRO": 199, "PRO_PLUS": 399, "ULTRA": 1599}


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def subscribe(self, user_id: str, plan: str):
        """訂閱方案。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        current_plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        current_status = user.subscription_status.value if hasattr(user.subscription_status, 'value') else str(user.subscription_status)

        # Cancelled user trying to re-subscribe before expiry
        if current_status == "cancelled" and current_plan == plan and user.next_billing_date:
            now = datetime.now(timezone.utc)
            if user.next_billing_date > now:
                return {"error": True, "status_code": 400, "message": f"您的 {plan} 方案尚未到期，請等待到期後再訂閱"}

        # Active user trying to subscribe same plan
        if current_plan == plan and current_status == "active":
            return {"error": True, "status_code": 400, "message": "您已訂閱此方案"}

        return {"message": "訂閱成功"}

    def get_subscription_info(self, user_id: str):
        """查看訂閱資訊。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        fee = PLAN_FEES.get(plan, 0)

        result = {
            "current_plan": plan,
            "monthly_fee": fee,
        }

        if user.next_billing_date:
            result["next_billing"] = user.next_billing_date.strftime("%Y-%m-%d")
        else:
            result["next_billing"] = None

        return result

    def upgrade(self, user_id: str, plan: str):
        """升級方案。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan_enum = SubscriptionPlan(plan)
        user.subscription_plan = plan_enum
        user.subscription_status = SubscriptionStatus.ACTIVE
        self.db.commit()

        return {"message": f"已升級至 {plan} 方案"}

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
