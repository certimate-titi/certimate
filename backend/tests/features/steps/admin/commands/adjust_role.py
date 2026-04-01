"""When 使用者將使用者 N 的角色調整為 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 將使用者 {user_key} 的角色調整為 "{role}"')
def step_impl(context, email, user_key, role):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    target_id = context.ids.get(user_key.strip())

    response = context.api_client.post(
        "/api/v1/admin/users/adjust-role",
        json={"target_user_id": target_id, "role": role},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
