"""When 使用者停權某使用者帳號（含原因） — Command (POST)"""

from behave import when


@when('使用者 "{email}" 停權使用者 {user_key} 的帳號，原因為 "{reason}"')
def step_impl(context, email, user_key, reason):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    target_id = context.ids.get(user_key.strip())

    response = context.api_client.post(
        "/api/v1/admin/users/suspend",
        json={"target_user_id": target_id, "reason": reason},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
