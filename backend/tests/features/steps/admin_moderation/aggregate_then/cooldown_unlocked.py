"""Then 使用者的冷卻狀態應為已解除 — Aggregate Then"""

import uuid

from behave import then

from app.models.ai_cooldown import AiCooldown
from app.models.user import User, UserStatus


@then('使用者 {user_key} 的冷卻狀態應為已解除')
def step_impl(context, user_key):
    db = context.db_session
    user_id_str = context.ids.get(user_key.strip())
    assert user_id_str, f"找不到使用者 ID: {user_key}"

    user_uuid = uuid.UUID(user_id_str)

    # Check no active cooldown remains
    cooldowns = db.query(AiCooldown).filter(AiCooldown.user_id == user_uuid).all()
    assert len(cooldowns) == 0, \
        f"使用者 {user_key} 仍有冷卻紀錄: {cooldowns}"

    # Check user status is no longer cooling
    user = db.query(User).filter(User.id == user_uuid).first()
    assert user is not None, f"找不到使用者 {user_key}"
    status_val = user.status.value if hasattr(user.status, "value") else str(user.status)
    assert status_val != "cooling", \
        f"使用者 {user_key} 的狀態應不為 cooling，實際: {user.status}"
