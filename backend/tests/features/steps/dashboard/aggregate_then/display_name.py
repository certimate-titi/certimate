"""Then 使用者顯示名稱驗證 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('使用者 "{email}" 的顯示名稱應為 "{expected_name}"')
def step_impl(context, email, expected_name):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    db.expire_all()
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 '{email}'"
    assert user.display_name == expected_name, \
        f"期望顯示名稱 '{expected_name}'，實際：{user.display_name}"
