"""When — 使用者啟動 14 天免費試用。"""

from behave import when


@when('使用者 "{email}" 啟動 14 天免費試用')
def step_start_trial(context, email):
    token = context.jwt_helper.generate_token(context.ids.get(email, email))
    context.last_response = context.api_client.post(
        "/api/v1/subscriptions/trial/start",
        headers={"Authorization": f"Bearer {token}"},
    )
