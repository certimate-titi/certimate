"""Then 使用者的角色應更新為 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('使用者 "{email}" 的角色應更新為 "{expected_role}"')
def step_impl(context, email, expected_role):
    db = context.db_session
    db.expire_all()
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 '{email}'"

    actual = user.role.value if hasattr(user.role, 'value') else str(user.role)

    assert actual == expected_role, (
        f"預期角色 '{expected_role}'，實際 '{actual}'"
    )
