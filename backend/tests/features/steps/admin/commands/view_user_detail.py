"""When 使用者查看某使用者的詳情 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看使用者 {user_key} 的詳情')
def step_impl(context, email, user_key):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    target_id = context.ids.get(user_key.strip())

    response = context.api_client.get(
        f"/api/v1/admin/users/{target_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
