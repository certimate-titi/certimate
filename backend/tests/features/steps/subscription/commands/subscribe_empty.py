"""When 使用者訂閱方案（空白目標方案） — Command (POST)"""

from behave import when


@when('使用者 "{email}" 訂閱  方案')
def step_subscribe_empty(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/subscriptions/subscribe",
        headers={"Authorization": f"Bearer {token}"},
        json={"plan": ""},
    )
    context.last_response = response
