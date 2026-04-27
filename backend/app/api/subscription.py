"""Subscription API — 訂閱管理。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.services.subscription_service import SubscriptionService
from app.services.trial_service import TrialService
from app.services.fup_service import FUPService
from app.services.admin_finance_service import AdminFinanceService

router = APIRouter(prefix="/subscriptions")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


class SubscribePlanRequest(BaseModel):
    plan: str


@router.post("/subscribe")
def subscribe(
    body: SubscribePlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """subscribe。

    此 endpoint 對應 `subscribe` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = SubscriptionService(db)
    result = service.subscribe(user_id=user_id, plan=body.plan)
    return _handle_result(result)


@router.get("")
def get_subscription_info(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get subscription info。

    此 endpoint 對應 `get_subscription_info` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = SubscriptionService(db)
    result = service.get_subscription_info(user_id=user_id)
    return _handle_result(result)


@router.post("/upgrade")
def upgrade(
    body: SubscribePlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """upgrade。

    此 endpoint 對應 `upgrade` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = SubscriptionService(db)
    result = service.upgrade(user_id=user_id, plan=body.plan)
    return _handle_result(result)


@router.post("/downgrade")
def downgrade(
    body: SubscribePlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """downgrade。

    此 endpoint 對應 `downgrade` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = SubscriptionService(db)
    result = service.downgrade(user_id=user_id, plan=body.plan)
    return _handle_result(result)


@router.post("/cancel")
def cancel(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """cancel。

    此 endpoint 對應 `cancel` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = SubscriptionService(db)
    result = service.cancel(user_id=user_id)
    return _handle_result(result)


# ========== 14 天試用 ==========

@router.post("/trial/start")
def start_trial(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """start trial。

    此 endpoint 對應 `start_trial` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = TrialService(db)
    result = service.start_trial(user_id=user_id)
    return _handle_result(result)


@router.get("/trial/status")
def get_trial_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get trial status。

    此 endpoint 對應 `get_trial_status` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = TrialService(db)
    result = service.get_trial_status(user_id=user_id)
    return _handle_result(result)


@router.post("/trial/convert")
def convert_trial_to_paid(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """convert trial to paid。

    此 endpoint 對應 `convert_trial_to_paid` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = TrialService(db)
    result = service.convert_to_paid(user_id=user_id)
    return _handle_result(result)


# ========== FUP ==========

@router.get("/fup/check")
def check_fup(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """check fup。

    此 endpoint 對應 `check_fup` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = FUPService(db)
    result = service.check_daily_usage(user_id=user_id)
    return _handle_result(result)


@router.get("/invoices")
def get_invoices(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get invoices。

    此 endpoint 對應 `get_invoices` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = SubscriptionService(db)
    result = service.get_invoices(user_id=user_id)
    return _handle_result(result)


# ========== Refund Request ==========

class RefundRequestBody(BaseModel):
    transaction_id: str
    amount: float
    reason: str | None = None


@router.post("/refund-request")
def request_refund(
    body: RefundRequestBody,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """request refund。

    此 endpoint 對應 `request_refund` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminFinanceService(db)
    result = service.request_refund(
        user_id=user_id,
        transaction_id=body.transaction_id,
        amount=body.amount,
        reason=body.reason,
    )
    return _handle_result(result)


# ========== Coupon Validation ==========

class ValidateCouponBody(BaseModel):
    code: str
    plan: str
    amount: float


@router.post("/coupons/validate")
def validate_coupon(
    body: ValidateCouponBody,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """validate coupon。

    此 endpoint 對應 `validate_coupon` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminFinanceService(db)
    result = service.validate_coupon(
        code=body.code,
        plan=body.plan,
        amount=body.amount,
    )
    return _handle_result(result)
