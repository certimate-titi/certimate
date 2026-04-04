"""Subscription API — 訂閱管理。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.services.subscription_service import SubscriptionService
from app.services.trial_service import TrialService
from app.services.fup_service import FUPService

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
    service = SubscriptionService(db)
    result = service.subscribe(user_id=user_id, plan=body.plan)
    return _handle_result(result)


@router.get("")
def get_subscription_info(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = SubscriptionService(db)
    result = service.get_subscription_info(user_id=user_id)
    return _handle_result(result)


@router.post("/upgrade")
def upgrade(
    body: SubscribePlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = SubscriptionService(db)
    result = service.upgrade(user_id=user_id, plan=body.plan)
    return _handle_result(result)


@router.post("/downgrade")
def downgrade(
    body: SubscribePlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = SubscriptionService(db)
    result = service.downgrade(user_id=user_id, plan=body.plan)
    return _handle_result(result)


@router.post("/cancel")
def cancel(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = SubscriptionService(db)
    result = service.cancel(user_id=user_id)
    return _handle_result(result)


# ========== 14 天試用 ==========

@router.post("/trial/start")
def start_trial(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = TrialService(db)
    result = service.start_trial(user_id=user_id)
    return _handle_result(result)


@router.get("/trial/status")
def get_trial_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = TrialService(db)
    result = service.get_trial_status(user_id=user_id)
    return _handle_result(result)


@router.post("/trial/convert")
def convert_trial_to_paid(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = TrialService(db)
    result = service.convert_to_paid(user_id=user_id)
    return _handle_result(result)


# ========== FUP ==========

@router.get("/fup/check")
def check_fup(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = FUPService(db)
    result = service.check_daily_usage(user_id=user_id)
    return _handle_result(result)


@router.get("/invoices")
def get_invoices(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = SubscriptionService(db)
    result = service.get_invoices(user_id=user_id)
    return _handle_result(result)
