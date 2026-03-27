"""When 使用者搜尋資源列表 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 以關鍵字 "{keyword}" 搜尋資源列表')
def step_impl(context, email, keyword):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/resource-library?keyword={keyword}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
