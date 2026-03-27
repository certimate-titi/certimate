"""When 使用者查詢自己的資源列表 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查詢自己的資源列表')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/resource-library",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
