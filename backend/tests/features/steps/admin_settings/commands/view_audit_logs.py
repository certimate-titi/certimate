"""When 使用者查看審計日誌 — Command"""

from behave import when


@when('使用者 "{email}" 查看審計日誌')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/admin/system-settings/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
