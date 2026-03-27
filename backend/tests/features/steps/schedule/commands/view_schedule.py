"""When 使用者查看學習排程建議 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看學習排程建議')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/schedule/recommendations",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
