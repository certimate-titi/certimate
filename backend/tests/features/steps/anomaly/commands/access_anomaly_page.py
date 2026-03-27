"""When 使用者存取異常維修管理頁面 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 存取異常維修管理頁面')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/admin/anomalies",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
