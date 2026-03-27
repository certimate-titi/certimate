"""When 使用者查看 AI 濫用監控面板 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看 AI 濫用監控面板')
def step_impl(context, email):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    response = context.api_client.get(
        "/api/v1/admin/moderation/ai-abuse",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
