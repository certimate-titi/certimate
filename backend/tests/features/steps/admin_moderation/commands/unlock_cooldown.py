"""When 使用者解除某使用者的 AI 冷卻狀態 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 解除使用者 {user_key} 的 AI 冷卻狀態')
def step_impl(context, email, user_key):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    target_id = context.ids.get(user_key.strip())

    response = context.api_client.post(
        f"/api/v1/admin/moderation/ai-abuse/{target_id}/unlock",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
