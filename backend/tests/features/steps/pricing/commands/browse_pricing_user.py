"""When 使用者瀏覽定價比較頁 — Command"""

from behave import when


@when('使用者 "{email}" 瀏覽定價比較頁')
def step_impl(context, email):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/pricing",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
