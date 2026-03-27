"""Then 使用者 N 的狀態應為 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('使用者 {user_key} 的狀態應為 "{expected_status}"')
def step_impl(context, user_key, expected_status):
    db = context.db_session
    target_id = uuid.UUID(context.ids[user_key.strip()])

    user = db.query(User).filter_by(id=target_id).first()
    db.refresh(user)
    actual = user.status.value if hasattr(user.status, "value") else str(user.status)
    assert actual == expected_status, \
        f"預期狀態 '{expected_status}'，實際 '{actual}'"
