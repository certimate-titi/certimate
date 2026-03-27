"""平台管理後台 — 財務管理 Service。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, SubscriptionPlan
from app.models.transaction import Transaction
from app.models.refund import Refund
from app.models.coupon import Coupon
from app.models.audit_log import AdminAuditLog


def _get_role(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _get_plan(user: User) -> str:
    return user.subscription_plan.value if hasattr(user.subscription_plan, "value") else str(user.subscription_plan)


class AdminFinanceService:
    def __init__(self, db: Session):
        self.db = db

    def _get_user(self, user_id: str) -> User | None:
        return self.db.query(User).filter_by(id=uuid.UUID(user_id)).first()

    def _require_admin(self, user_id: str) -> dict | None:
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
            return {"error": True, "status_code": 403, "message": "權限不足，僅 super_admin 可執行此操作"}
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

    # ── Subscription Distribution ─────────────────────────────────────────────

    def get_subscription_distribution(self, actor_id: str) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        distribution = {}
        for plan in SubscriptionPlan:
            count = (
                self.db.query(User)
                .filter(User.subscription_plan == plan)
                .count()
            )
            distribution[plan.value] = count

        return {
            "distribution": distribution,
        }

    # ── Transactions ──────────────────────────────────────────────────────────

    def list_transactions(self, actor_id: str, status: str | None = None) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        query = self.db.query(Transaction)
        if status:
            query = query.filter(Transaction.status == status)

        txns = query.order_by(Transaction.created_at.desc()).all()

        return {
            "transactions": [
                {
                    "transaction_id": t.merchant_trade_no,
                    "user_id": str(t.user_id),
                    "amount": float(t.amount),
                    "plan": t.target_plan,
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in txns
            ]
        }

    # ── Refunds ───────────────────────────────────────────────────────────────

    def approve_refund(self, actor_id: str, refund_id: str) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        refund = self.db.query(Refund).filter_by(refund_id=refund_id).first()
        if not refund:
            return {"error": True, "status_code": 404, "message": "退款申請不存在"}

        if refund.status != "pending":
            return {"error": True, "status_code": 400, "message": "只能核准待審核的退款"}

        refund.status = "approved"
        self.db.commit()
        self.db.refresh(refund)

        self._write_audit_log(
            admin_id=actor_id,
            action="approve_refund",
            target_type="refund",
            target_id=str(refund.id),
            details={"refund_id": refund_id, "amount": float(refund.amount), "summary": f"退款 {float(refund.amount)} TWD"},
        )

        return {"success": True, "refund_id": refund_id, "status": "approved"}

    def reject_refund(self, actor_id: str, refund_id: str, reason: str) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        refund = self.db.query(Refund).filter_by(refund_id=refund_id).first()
        if not refund:
            return {"error": True, "status_code": 404, "message": "退款申請不存在"}

        if refund.status != "pending":
            return {"error": True, "status_code": 400, "message": "只能駁回待審核的退款"}

        refund.status = "rejected"
        refund.reason = reason
        self.db.commit()
        self.db.refresh(refund)

        self._write_audit_log(
            admin_id=actor_id,
            action="reject_refund",
            target_type="refund",
            target_id=str(refund.id),
            details={"refund_id": refund_id, "reason": reason},
        )

        return {"success": True, "refund_id": refund_id, "status": "rejected"}

    # ── Coupons ───────────────────────────────────────────────────────────────

    def create_coupon(self, actor_id: str, data: dict) -> dict:
        err = self._require_super_admin(actor_id)
        if err:
            return err

        code = (data.get("code") or "").strip()
        discount_type = (data.get("discount_type") or "").strip()
        discount_value_raw = data.get("discount_value")
        discount_value_str = str(discount_value_raw).strip() if discount_value_raw is not None else ""

        if not code:
            return {"error": True, "status_code": 422, "message": "必要參數未提供"}
        if not discount_type:
            return {"error": True, "status_code": 422, "message": "必要參數未提供"}
        if not discount_value_str:
            return {"error": True, "status_code": 422, "message": "必要參數未提供"}

        existing = self.db.query(Coupon).filter_by(code=code).first()
        if existing:
            return {"error": True, "status_code": 409, "message": "優惠碼已存在"}

        coupon = Coupon(
            code=code,
            discount_type=discount_type,
            discount_value=float(discount_value_str),
            applicable_plans=data.get("applicable_plans"),
            max_uses=int(data["max_uses"]) if data.get("max_uses") else None,
            max_uses_per_user=int(data["max_uses_per_user"]) if data.get("max_uses_per_user") else None,
            used_count=0,
            status="active",
        )
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)

        return {
            "success": True,
            "code": coupon.code,
            "status": coupon.status,
            "used_count": coupon.used_count,
        }

    def get_coupon(self, actor_id: str, code: str) -> dict:
        err = self._require_admin(actor_id)
        if err:
            return err

        coupon = self.db.query(Coupon).filter_by(code=code).first()
        if not coupon:
            return {"error": True, "status_code": 404, "message": "優惠碼不存在"}

        return {
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
            "applicable_plans": coupon.applicable_plans,
            "max_uses": coupon.max_uses,
            "max_uses_per_user": coupon.max_uses_per_user,
            "used_count": coupon.used_count,
            "status": coupon.status,
        }
