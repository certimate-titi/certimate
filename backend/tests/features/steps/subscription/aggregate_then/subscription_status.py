"""Then 使用者的訂閱狀態應為 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('使用者 "{email}" 的訂閱狀態應為 "{expected_status}"')
def step_impl(context, email, expected_status):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    db.refresh(user)
    actual = user.subscription_status.value if hasattr(user.subscription_status, 'value') else str(user.subscription_status)
    assert actual == expected_status, \
        f"預期訂閱狀態 '{expected_status}'，實際 '{actual}'"
