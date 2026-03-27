"""When 使用者完成方案訂閱付款 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 完成 "{plan}" 方案訂閱付款')
def step_impl(context, email, plan):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/subscriptions/upgrade",
        headers={"Authorization": f"Bearer {token}"},
        json={"plan": plan},
    )
    context.last_response = response
