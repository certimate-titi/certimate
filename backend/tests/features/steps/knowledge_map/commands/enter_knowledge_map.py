"""When 使用者進入知識心智圖頁面 — Query"""

from behave import when


@when('使用者 "{email}" 進入知識心智圖頁面')
def step_impl(context, email):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/knowledge-map/layout",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
