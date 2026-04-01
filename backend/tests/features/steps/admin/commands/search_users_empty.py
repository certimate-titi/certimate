"""When 使用者搜尋用戶（空關鍵字）— Command (GET)"""

from behave import when


@when('使用者 "{email}" 搜尋用戶，關鍵字為 ""')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/admin/users",
        params={"keyword": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
