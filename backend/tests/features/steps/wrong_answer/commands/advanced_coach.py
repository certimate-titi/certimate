"""When 使用者請求進階 AI 教練分析 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 請求進階 AI 教練分析')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/wrong-answers/advanced-coach",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
