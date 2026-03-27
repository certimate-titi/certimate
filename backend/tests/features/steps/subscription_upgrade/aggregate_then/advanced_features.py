"""Then 使用者應解鎖高階教練 / Vision OCR 額度 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User
from app.models.plan_quota import PlanQuota


_USER_PLAN_MAP = {
    "FREE": "FREE",
    "PRO": "PRO_199",
    "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599",
}


@then('使用者 "{email}" 應解鎖高階教練功能')
def step_impl(context, email):
    db = context.db_session
    db.expire_all()
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()
    plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)

    # PRO_PLUS 和 ULTRA 可以使用高階教練
    assert plan_val in ("PRO_PLUS", "ULTRA"), (
        f"預期方案為 PRO_PLUS 或 ULTRA 以解鎖高階教練，實際方案 '{plan_val}'"
    )


@then('使用者 "{email}" 的 Vision OCR 額度應為 {count:d}')
def step_impl_vision(context, email, count):
    db = context.db_session
    db.expire_all()
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()
    plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    plan_key = _USER_PLAN_MAP.get(plan_val, plan_val)

    quota = db.query(PlanQuota).filter_by(plan=plan_key).first()
    assert quota is not None, f"找不到方案 '{plan_key}' 的配額設定"
    assert quota.monthly_vision_pages == count, (
        f"預期 Vision OCR 額度 {count}，實際 {quota.monthly_vision_pages}"
    )
