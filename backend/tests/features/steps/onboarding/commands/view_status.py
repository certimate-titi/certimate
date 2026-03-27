"""When 使用者查看 Onboarding 狀態 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看 Onboarding 狀態')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/onboarding/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
