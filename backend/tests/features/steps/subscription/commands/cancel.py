"""When 使用者取消訂閱 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 取消訂閱')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/subscriptions/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
