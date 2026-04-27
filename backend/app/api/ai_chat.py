"""AI Chat API — AI 對話（含 FUP soft cap 檢查 + 限額檢查）。"""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.models.user import User, SubscriptionPlan
from app.models.user_usage import UserUsage
from app.models.plan_quota import PlanQuota
from app.models.audit_log import AdminAuditLog

logger = logging.getLogger("certimate.ai_chat")

router = APIRouter(prefix="/ai")

DAILY_SOFT_CAP = 1000

PLAN_DB_TO_DISPLAY = {
    "FREE": "FREE", "PRO": "PRO_199", "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599", "EDU": "EDU",
}

UPGRADE_PATH = {
    "FREE": "PRO_199",
    "PRO_199": "PRO_PLUS_399",
    "PRO_PLUS_399": "ULTRA_1599",
}

PLAN_FEES = {
    "FREE": 0, "PRO_199": 199, "PRO_PLUS_399": 399, "ULTRA_1599": 1599,
}


class AiChatRequest(BaseModel):
    message: str
    context_type: str | None = None
    context_id: str | None = None


class AiCoachRequest(BaseModel):
    question: str | None = None


@router.post("/chat")
def ai_chat(
    body: AiChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """ai chat。

    此 endpoint 對應 `ai_chat` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()

    plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    plan_display = PLAN_DB_TO_DISPLAY.get(plan, plan)

    # Check daily AI chat limit
    quota = db.query(PlanQuota).filter_by(plan=plan_display).first()
    if not quota:
        quota = db.query(PlanQuota).filter_by(plan=plan).first()

    daily_limit = quota.daily_ai_chats if quota else 3
    period = datetime.now().strftime("%Y-%m")
    usage = db.query(UserUsage).filter_by(user_id=user_uuid, period=period).first()
    daily_used = usage.daily_ai_chats_used if usage else 0

    # Check hard limit for non-ULTRA plans
    if daily_limit is not None and daily_used >= daily_limit and plan != "ULTRA":
        upgrade_to = UPGRADE_PATH.get(plan_display)
        guidance = {
            "current_plan": plan_display,
            "limit_type": "daily_ai_chat",
            "current_limit": daily_limit,
        }
        if upgrade_to:
            uq = db.query(PlanQuota).filter_by(plan=upgrade_to).first()
            guidance["upgrade_to"] = upgrade_to
            guidance["upgrade_limit"] = uq.daily_ai_chats if uq else None
            guidance["monthly_fee"] = PLAN_FEES.get(upgrade_to)

        raise HTTPException(
            status_code=400,
            detail={
                "message": "已達今日 AI 對話上限",
                "upgrade_guidance": guidance,
            },
        )

    # Check FUP soft cap for ULTRA users
    if plan == "ULTRA" and daily_used >= DAILY_SOFT_CAP:
        alert_log = AdminAuditLog(
            admin_id=user_uuid,
            action="fup_soft_cap_triggered",
            target_type="user",
            target_id=user_uuid,
            details={"daily_usage": daily_used + 1, "soft_cap": DAILY_SOFT_CAP},
        )
        db.add(alert_log)
        db.commit()
        logger.warning("FUP soft cap exceeded: user=%s, usage=%d", user_id, daily_used + 1)

    return {
        "message": "AI chat response placeholder",
        "request_message": body.message,
    }


@router.post("/coach")
def ai_coach(
    body: AiCoachRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """高階教練功能 — PRO_PLUS 以上方案專屬。"""
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()

    plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)

    if plan not in ("PRO_PLUS", "ULTRA"):
        has_used_trial = bool(user.has_used_trial) if hasattr(user, 'has_used_trial') else False
        raise HTTPException(
            status_code=403,
            detail={
                "message": "高階教練為 PRO_PLUS 以上方案專屬功能",
                "upgrade_guidance": {
                    "required_plan": "PRO_PLUS_399",
                    "feature_name": "高階教練",
                },
            },
        )

    return {"message": "AI coach response placeholder"}
