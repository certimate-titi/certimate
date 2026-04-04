"""Then 使用者訂閱方案應自動降級為 FREE — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('使用者 {user_id_key} 的訂閱方案應自動降級為 "{expected_plan}"')
def step_impl(context, user_id_key, expected_plan):
    db = context.db_session
    db.expire_all()

    key = user_id_key.strip().strip('"')
    user_uuid = uuid.UUID(context.ids[key])
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 {key}"
    actual = user.subscription_plan.value if hasattr(user.subscription_plan, "value") else str(user.subscription_plan)
    assert actual == expected_plan, \
        f"使用者 {key} 訂閱方案應為 '{expected_plan}'，實際 '{actual}'"
