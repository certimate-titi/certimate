"""When 使用者搜尋用戶 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 搜尋用戶，關鍵字為 "{keyword}"')
def step_impl(context, email, keyword):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/admin/users",
        params={"keyword": keyword},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
