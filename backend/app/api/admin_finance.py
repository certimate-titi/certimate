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
