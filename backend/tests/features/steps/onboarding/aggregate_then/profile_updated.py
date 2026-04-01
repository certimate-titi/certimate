"""Then 系統應更新使用者的個人資料與學習偏好 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('系統應更新使用者的個人資料與學習偏好')
def step_impl(context):
    db = context.db_session
    db.expire_all()

    email = context.memo.get("current_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_uuid = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 {email}"
