"""Then 使用者的 Onboarding 狀態應標記為已完成 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('使用者的 Onboarding 狀態應標記為「已完成」')
def step_impl(context):
    db = context.db_session
    email = context.memo.get("current_email")
    user_uuid = uuid.UUID(context.ids[email])

    db.expire_all()
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 {email}"
    assert user.onboarding_completed is True, \
        f"預期 onboarding_completed=True，實際: {user.onboarding_completed}"
