"""Then 使用者的每日 AI 對話限額應為 N — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User
from app.models.plan_quota import PlanQuota


_USER_PLAN_MAP = {
    "FREE": "FREE",
    "PRO": "PRO_199",
    "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599",
    "EDU": "EDU",
}


@then('使用者 "{email}" 的每日 AI 對話限額應為 {count:d}')
def step_impl(context, email, count):
    db = context.db_session
    db.expire_all()
    if email in context.ids:
        user_uuid = uuid.UUID(context.ids[email])
        user = db.query(User).filter_by(id=user_uuid).first()
    else:
        user = db.query(User).filter_by(email=email).first()
    assert user is not None, f"找不到使用者 '{email}'"

    plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    plan_key = _USER_PLAN_MAP.get(plan_val, plan_val)

    quota = db.query(PlanQuota).filter_by(plan=plan_key).first()
    assert quota is not None, f"找不到方案 '{plan_key}' 的配額設定"
    assert quota.daily_ai_chats == count, (
        f"預期每日 AI 對話限額 {count}，實際 {quota.daily_ai_chats}"
    )
