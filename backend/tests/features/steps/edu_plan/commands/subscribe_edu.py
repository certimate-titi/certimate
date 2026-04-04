"""When — 一般用戶嘗試訂閱 EDU 方案。"""

from behave import when


@when('使用者 "{email}" 嘗試訂閱 "EDU" 方案')
def step_subscribe_edu(context, email):
    token = context.jwt_helper.generate_token(context.ids.get(email, email))
    context.last_response = context.api_client.post(
        "/api/v1/subscriptions/subscribe",
        json={"plan": "EDU"},
        headers={"Authorization": f"Bearer {token}"},
    )
