"""Then 使用者 N 的訂閱方案應為 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User, SubscriptionPlan

# Plan display name mapping (DB value → marketing display name)
_PLAN_DISPLAY_NAMES = {
    SubscriptionPlan.FREE: "FREE",
    SubscriptionPlan.PRO: "PRO_199",
    SubscriptionPlan.PRO_PLUS: "PRO_PLUS_399",
    SubscriptionPlan.ULTRA: "ULTRA_1599",
}


@then('使用者 {user_key} 的訂閱方案應為 "{expected_plan}"')
def step_impl(context, user_key, expected_plan):
    db = context.db_session
    target_id = uuid.UUID(context.ids[user_key.strip()])

    user = db.query(User).filter_by(id=target_id).first()
    db.refresh(user)
    # Use display name (PRO_199, PRO_PLUS_399, ULTRA_1599) for comparison
    plan_enum = user.subscription_plan
    actual = _PLAN_DISPLAY_NAMES.get(plan_enum, plan_enum.value if hasattr(plan_enum, "value") else str(plan_enum))
    assert actual == expected_plan, \
        f"預期訂閱方案 '{expected_plan}'，實際 '{actual}'"
