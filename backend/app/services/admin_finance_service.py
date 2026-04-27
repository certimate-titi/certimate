"""平台管理後台 — 財務管理 Service。"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, SubscriptionPlan
from app.models.transaction import Transaction
from app.models.refund import Refund
from app.models.coupon import Coupon
from app.models.audit_log import AdminAuditLog


def _get_role(user: User) -> str:
    """取得 role。"""
    return user.role.value if hasattr(user.role, "value") else str(user.role)


_PLAN_DISPLAY = {
    SubscriptionPlan.FREE: "FREE",
    SubscriptionPlan.PRO: "PRO_199",
    SubscriptionPlan.PRO_PLUS: "PRO_PLUS_399",
    SubscriptionPlan.ULTRA: "ULTRA_1599",
}


def _get_plan(user: User) -> str:
    """取得 plan。"""
    return user.subscription_plan.value if hasattr(user.subscription_plan, "value") else str(user.subscription_plan)


class AdminFinanceService:
    """Admin Finance Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db

    def _get_user(self, user_id: str) -> User | None:
        """取得 user。"""
        return self.db.query(User).filter_by(id=uuid.UUID(user_id)).first()

    def _require_admin(self, user_id: str) -> dict | None:
        """ require admin。"""
        user = self._get_user(user_id)
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        role = _get_role(user)
        if role not in ("admin", "super_admin"):
            return {"error": True, "status_code": 403, "message": "權限不足，無法存取管理後台"}
        return None

    def _require_super_admin(self, user_id: str) -> dict | None:
        """ require super admin。"""
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
        """ write audit log。"""
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
        """取得 subscription distribution。"""
        err = self._require_admin(actor_id)
        if err:
            return err

        distribution = {}
        for plan in SubscriptionPlan:
            count = (
                self.db.query(User)
                .filter(User.subscription_plan == plan)
                .filter(User.role.notin_([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
                .count()
            )
            display_key = _PLAN_DISPLAY.get(plan, plan.value)
            distribution[display_key] = count

        # Build 30-day MRR trend using Transaction data
        now = datetime.now(timezone.utc)
        mrr_trend = []
        for offset in range(29, -1, -1):
            day = now - timedelta(days=offset)
            day_str = day.strftime("%Y-%m-%d")
            # Sum successful transactions for the day
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            from sqlalchemy import func as sqlfunc
            mrr = self.db.query(sqlfunc.coalesce(sqlfunc.sum(Transaction.amount), 0)).filter(
                Transaction.status == "success",
                Transaction.created_at >= day_start,
                Transaction.created_at < day_end,
            ).scalar() or 0
            mrr_trend.append({"date": day_str, "mrr": float(mrr)})

        return {
            "distribution": distribution,
            "mrr_trend": mrr_trend,
        }

    # ── Transactions ──────────────────────────────────────────────────────────

    def list_transactions(self, actor_id: str, status: str | None = None, search: str | None = None) -> dict:
        """列出 transactions。"""
        err = self._require_admin(actor_id)
        if err:
            return err

        query = self.db.query(Transaction)
        if status:
            query = query.filter(Transaction.status == status)
        if search:
            query = query.filter(Transaction.merchant_trade_no.ilike(f"%{search}%"))

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

    def export_finance_report(self, actor_id: str) -> dict:
        """匯出 finance report。"""
        err = self._require_admin(actor_id)
        if err:
            return err

        txns = self.db.query(Transaction).order_by(Transaction.created_at.desc()).all()
        total_revenue = sum(float(t.amount) for t in txns if t.status == "success")
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
            ],
            "summary": {
                "total_transactions": len(txns),
                "total_revenue": total_revenue,
                "success_count": sum(1 for t in txns if t.status == "success"),
            },
        }

    # ── Refunds ───────────────────────────────────────────────────────────────

    def list_refunds(self, actor_id: str, status: str | None = None) -> dict:
        """列出 refunds。"""
        err = self._require_admin(actor_id)
        if err:
            return err

        query = self.db.query(Refund)
        if status:
            query = query.filter(Refund.status == status)
        refunds = query.order_by(Refund.created_at.desc()).all()

        items = []
        for r in refunds:
            user = self.db.query(User).filter_by(id=r.user_id).first()
            items.append({
                "id": str(r.id),
                "refund_id": r.refund_id,
                "user_email": user.email if user else "",
                "transaction_id": r.transaction_id,
                "amount": float(r.amount),
                "status": r.status,
                "reason": r.reason,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return {"refunds": items}

    def approve_refund(self, actor_id: str, refund_id: str) -> dict:
        """approve refund。"""
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
            details={"refund_id": refund_id, "amount": float(refund.amount), "summary": f"退款 {int(refund.amount)} TWD"},
        )

        return {"success": True, "refund_id": refund_id, "status": "approved"}

    def reject_refund(self, actor_id: str, refund_id: str, reason: str) -> dict:
        """reject refund。"""
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
        """建立 coupon。"""
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

    def list_coupons(self, actor_id: str) -> dict:
        """列出 coupons。"""
        err = self._require_admin(actor_id)
        if err:
            return err
        coupons = self.db.query(Coupon).order_by(Coupon.created_at.desc()).all()
        return {
            "coupons": [
                {
                    "id": str(c.id),
                    "code": c.code,
                    "discount_type": c.discount_type,
                    "discount_value": float(c.discount_value),
                    "applicable_plans": c.applicable_plans,
                    "max_uses": c.max_uses,
                    "max_uses_per_user": c.max_uses_per_user,
                    "used_count": c.used_count,
                    "status": c.status,
                }
                for c in coupons
            ]
        }

    def request_refund(self, user_id: str, transaction_id: str, amount: float, reason: str | None) -> dict:
        """request refund。"""
        user = self._get_user(user_id)
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        txn = self.db.query(Transaction).filter_by(merchant_trade_no=transaction_id).first()
        if not txn:
            return {"error": True, "status_code": 404, "message": "找不到對應交易"}
        if txn.user_id != user.id:
            return {"error": True, "status_code": 403, "message": "無法對他人交易申請退款"}

        existing = self.db.query(Refund).filter_by(transaction_id=transaction_id).first()
        if existing and existing.status == "pending":
            return {"error": True, "status_code": 409, "message": "此交易已有待審核的退款申請"}

        import secrets
        refund_id = "RF-" + secrets.token_hex(6).upper()
        refund = Refund(
            refund_id=refund_id,
            user_id=user.id,
            transaction_id=transaction_id,
            amount=amount,
            status="pending",
            reason=reason,
        )
        self.db.add(refund)
        self.db.commit()
        self.db.refresh(refund)

        return {
            "success": True,
            "refund_id": refund_id,
            "status": "pending",
        }

    def validate_coupon(self, code: str, plan: str, amount: float) -> dict:
        """驗證 coupon。"""
        coupon = self.db.query(Coupon).filter_by(code=code).first()
        if not coupon or coupon.status != "active":
            return {"error": True, "status_code": 404, "message": "優惠碼無效"}
        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            return {"error": True, "status_code": 410, "message": "優惠碼已額滿"}
        if coupon.applicable_plans and plan not in coupon.applicable_plans.split(","):
            return {"error": True, "status_code": 400, "message": "此優惠碼不適用於所選方案"}

        discount_value = float(coupon.discount_value)
        if coupon.discount_type == "percent":
            discount = round(amount * discount_value / 100, 2)
        else:
            discount = discount_value
        final_amount = max(amount - discount, 0)

        return {
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": discount_value,
            "discount_amount": discount,
            "original_amount": amount,
            "final_amount": final_amount,
        }
