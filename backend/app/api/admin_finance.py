"""平台管理後台 — 財務管理 API。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.services.admin_finance_service import AdminFinanceService

router = APIRouter(prefix="/admin/finance")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


# ── Subscription Distribution ─────────────────────────────────────────────────

@router.get("/subscription-distribution")
def get_subscription_distribution(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminFinanceService(db)
    result = service.get_subscription_distribution(actor_id=user_id)
    return _handle_result(result)


# ── Transactions ──────────────────────────────────────────────────────────────

@router.get("/transactions")
def list_transactions(
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminFinanceService(db)
    result = service.list_transactions(actor_id=user_id, status=status)
    return _handle_result(result)


# ── Refunds ───────────────────────────────────────────────────────────────────

@router.get("/refunds")
def list_refunds(
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminFinanceService(db)
    result = service.list_refunds(actor_id=user_id, status=status)
    return _handle_result(result)


@router.post("/refunds/{refund_id}/approve")
def approve_refund(
    refund_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminFinanceService(db)
    result = service.approve_refund(actor_id=user_id, refund_id=refund_id)
    return _handle_result(result)


class RejectRefundRequest(BaseModel):
    reason: str


@router.post("/refunds/{refund_id}/reject")
def reject_refund(
    refund_id: str,
    body: RejectRefundRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminFinanceService(db)
    result = service.reject_refund(actor_id=user_id, refund_id=refund_id, reason=body.reason)
    return _handle_result(result)


# ── Coupons ───────────────────────────────────────────────────────────────────

class CreateCouponRequest(BaseModel):
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    applicable_plans: Optional[str] = None
    max_uses: Optional[int] = None
    max_uses_per_user: Optional[int] = None


@router.get("/coupons")
def list_coupons(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminFinanceService(db)
    result = service.list_coupons(actor_id=user_id)
    return _handle_result(result)


@router.post("/coupons")
def create_coupon(
    body: CreateCouponRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminFinanceService(db)
    result = service.create_coupon(actor_id=user_id, data=body.model_dump())
    return _handle_result(result)


@router.get("/coupons/{code}")
def get_coupon(
    code: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AdminFinanceService(db)
    result = service.get_coupon(actor_id=user_id, code=code)
    return _handle_result(result)


# ── Finance Overview & MRR Trend ─────────────────────────────────────────────

@router.get("/overview")
def get_finance_overview(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """財務概覽：MRR、ARPU、LTV、Churn Rate。"""
    from sqlalchemy import func
    from app.models.user import User, SubscriptionPlan

    plan_prices = {"PRO_199": 199, "PRO_PLUS_399": 399, "ULTRA_1599": 1599}
    total_users = db.query(func.count(User.id)).scalar() or 1
    paid_users = 0
    mrr = 0

    for plan_val, price in plan_prices.items():
        try:
            plan_enum = SubscriptionPlan(plan_val)
            count = db.query(func.count(User.id)).filter(User.subscription_plan == plan_enum).scalar() or 0
            paid_users += count
            mrr += count * price
        except ValueError:
            pass

    arpu = round(mrr / max(paid_users, 1))
    ltv = arpu * 12  # estimate 12 months average retention

    # Churn: users who downgraded to FREE in last 30 days / paid users last month
    # Real data from audit_logs where action='adjust_subscription' and details contains '→ FREE'
    from sqlalchemy import text as _text
    try:
        churned = db.execute(_text(
            "SELECT count(*) FROM admin_audit_logs WHERE action='adjust_subscription' "
            "AND details LIKE '%→ FREE%' AND created_at >= NOW() - INTERVAL '30 days'"
        )).scalar() or 0
        churn_rate = round(churned * 100 / max(paid_users, 1), 1)
    except Exception:
        churn_rate = 0.0

    return {
        "mrr": mrr,
        "arpu": arpu,
        "ltv": ltv,
        "churn_rate": churn_rate,
        "total_users": total_users,
        "paid_users": paid_users,
    }


@router.get("/mrr-trend")
def get_mrr_trend(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """MRR 趨勢：過去 6 個月。"""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func
    from app.models.user import User, SubscriptionPlan

    plan_prices = {"PRO_199": 199, "PRO_PLUS_399": 399, "ULTRA_1599": 1599}
    now = datetime.now(timezone.utc)
    trend = []

    for i in range(5, -1, -1):
        month_end = (now - timedelta(days=30 * i)).replace(hour=23, minute=59, second=59)
        month_name = month_end.strftime("%m月")
        month_mrr = 0

        for plan_val, price in plan_prices.items():
            try:
                plan_enum = SubscriptionPlan(plan_val)
                count = db.query(func.count(User.id)).filter(
                    User.subscription_plan == plan_enum,
                    User.created_at <= month_end,
                ).scalar() or 0
                month_mrr += count * price
            except ValueError:
                pass

        trend.append({"name": month_name, "mrr": month_mrr})

    return {"trend": trend}
