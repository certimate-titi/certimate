"""When 使用者嘗試使用高階教練功能 — Command"""

from behave import when


@when('使用者 "{email}" 嘗試使用高階教練功能')
def step_impl(context, email):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/ai/coach",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "test"},
    )
    context.last_response = response
