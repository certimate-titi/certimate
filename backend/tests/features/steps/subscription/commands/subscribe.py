"""When 使用者訂閱方案 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 訂閱 "{plan}" 方案')
def step_impl(context, email, plan):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/subscriptions/subscribe",
        headers={"Authorization": f"Bearer {token}"},
        json={"plan": plan},
    )
    context.last_response = response
