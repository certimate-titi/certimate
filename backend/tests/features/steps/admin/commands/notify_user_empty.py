"""When 使用者發送空白通知 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 發送通知給使用者 {user_key}，訊息為 ""')
def step_impl(context, email, user_key):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    target_id = context.ids.get(user_key.strip())

    response = context.api_client.post(
        f"/api/v1/admin/users/{target_id}/notify",
        json={"message": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
