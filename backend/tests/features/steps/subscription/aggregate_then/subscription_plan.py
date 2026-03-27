"""Then 使用者的訂閱方案應為 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('使用者 "{email}" 的訂閱方案應為 "{expected_plan}"')
def step_impl(context, email, expected_plan):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    db.refresh(user)
    actual = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    assert actual == expected_plan, \
        f"預期訂閱方案 '{expected_plan}'，實際 '{actual}'"
