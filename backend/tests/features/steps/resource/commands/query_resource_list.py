"""When 使用者查詢資源列表。"""

from behave import when


@when('使用者 "{email}" 查詢資源列表')
def step_impl(context, email):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"
    token = context.jwt_helper.create_token(user_id)
    response = context.api_client.get(
        "/api/v1/resources",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
