"""When 使用者透過 Email 將角色調整為 — Command (POST)"""

from behave import when


@when('使用者 "{actor_email}" 透過 Email "{target_email}" 將角色調整為 "{role}"')
def step_impl(context, actor_email, target_email, role):
    actor_id = context.ids[actor_email]
    token = context.jwt_helper.generate_token(actor_id)

    response = context.api_client.post(
        "/api/v1/admin/users/adjust-role",
        json={"email": target_email, "role": role},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
