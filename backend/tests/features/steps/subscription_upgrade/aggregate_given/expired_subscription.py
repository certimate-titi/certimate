"""Given 使用者的訂閱已到期且自動降級為 FREE — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User, SubscriptionPlan, SubscriptionStatus


@given('使用者 "{email}" 的訂閱已到期且自動降級為 FREE')
def step_impl(context, email):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()

    user.subscription_plan = SubscriptionPlan.FREE
    user.subscription_status = SubscriptionStatus.EXPIRED
    db.commit()

    # 記錄 Firebase Claims 更新
    if "firebase_claims" not in context.memo:
        context.memo["firebase_claims"] = {}
    context.memo["firebase_claims"][email] = {
        "plan": "FREE",
        "subscription_status": "expired",
    }
