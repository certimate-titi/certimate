"""When 使用者恢復使用者 N 的帳號 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 恢復使用者 {user_id:d} 的帳號')
def step_impl_by_id(context, email, user_id):
    return _activate(context, email, str(user_id))


@when('使用者 "{email}" 恢復使用者 "{user_key}" 的帳號')
def step_impl(context, email, user_key):
    return _activate(context, email, user_key)


def _activate(context, email, user_key):
    from app.models.user import User

    # 支援兩種格式：context.ids mapping 或直接查 DB by email
    actor_id = context.ids.get(email)
    if not actor_id:
        actor = context.db_session.query(User).filter(User.email == email).first()
        assert actor, f"找不到使用者 {email}"
        actor_id = str(actor.id)

    token = context.jwt_helper.generate_token(actor_id)

    target_id = context.ids.get(user_key.strip())
    if not target_id:
        target = context.db_session.query(User).filter(User.email == user_key.strip()).first()
        target_id = str(target.id) if target else None

    response = context.api_client.post(
        "/api/v1/admin/users/activate",
        json={"target_user_id": target_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
