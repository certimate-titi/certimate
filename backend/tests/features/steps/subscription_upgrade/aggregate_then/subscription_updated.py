"""Then 使用者的訂閱方案/狀態應更新 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


_PLAN_MAP = {
    "FREE": "FREE",
    "PRO_199": "PRO",
    "PRO_PLUS_399": "PRO_PLUS",
    "ULTRA_1599": "ULTRA",
}


@then('使用者 "{email}" 的訂閱方案應更新為 "{expected_plan}"')
def step_impl(context, email, expected_plan):
    db = context.db_session
    db.expire_all()
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()

    actual = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    expected_db = _PLAN_MAP.get(expected_plan, expected_plan)

    assert actual == expected_db, (
        f"預期訂閱方案 '{expected_db}'，實際 '{actual}'"
    )


@then('使用者 "{email}" 的訂閱狀態應更新為 "{expected_status}"')
def step_impl_status(context, email, expected_status):
    db = context.db_session
    db.expire_all()
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()

    actual = user.subscription_status.value if hasattr(user.subscription_status, 'value') else str(user.subscription_status)

    assert actual == expected_status, (
        f"預期訂閱狀態 '{expected_status}'，實際 '{actual}'"
    )
