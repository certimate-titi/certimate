"""When 使用者恢復使用者 N 的帳號 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 恢復使用者 {user_key} 的帳號')
def step_impl(context, email, user_key):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    target_id = context.ids.get(user_key.strip())

    response = context.api_client.post(
        "/api/v1/admin/users/activate",
        json={"target_user_id": target_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
