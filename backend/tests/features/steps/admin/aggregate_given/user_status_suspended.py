"""Given 使用者 N 的狀態為 — Aggregate Given (set user status in DB)"""

import uuid

from behave import given

from app.models.user import User, UserStatus


@given('使用者 {user_key} 的狀態為 "{status}"')
def step_impl(context, user_key, status):
    db = context.db_session
    target_id = uuid.UUID(context.ids[user_key.strip()])

    user = db.query(User).filter_by(id=target_id).first()
    assert user is not None, f"找不到使用者 {user_key}"

    status_map = {
        "active": UserStatus.ACTIVE,
        "suspended": UserStatus.SUSPENDED,
        "pending": UserStatus.PENDING,
        "cooling": UserStatus.COOLING,
        "deleted": UserStatus.DELETED,
    }
    user.status = status_map.get(status, status)
    db.commit()
