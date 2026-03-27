"""When 使用者匯出用戶 CSV — Command (GET)"""

from behave import when


@when('使用者 "{email}" 匯出用戶 CSV，篩選方案為 "{plan}"')
def step_impl(context, email, plan):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/admin/users/export",
        params={"plan": plan},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
