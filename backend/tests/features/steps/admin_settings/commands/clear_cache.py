"""When 使用者清理系統暫存檔 — Command"""

from behave import when


@when('使用者 "{email}" 清理系統暫存檔')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/admin/system-settings/clear-cache",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
