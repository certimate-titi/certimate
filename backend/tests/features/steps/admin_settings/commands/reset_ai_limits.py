"""When 使用者重置 AI 流量限制 — Command"""

from behave import when


@when('使用者 "{email}" 重置 AI 流量限制')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/admin/system-settings/reset-ai-limits",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
