"""Then 使用者 N 的角色應為 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('使用者 {user_key} 的角色應為 "{expected_role}"')
def step_impl(context, user_key, expected_role):
    db = context.db_session
    target_id = uuid.UUID(context.ids[user_key.strip()])

    user = db.query(User).filter_by(id=target_id).first()
    db.refresh(user)
    actual = user.role.value if hasattr(user.role, "value") else str(user.role)
    assert actual == expected_role, \
        f"預期角色 '{expected_role}'，實際 '{actual}'"
