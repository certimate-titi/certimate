"""When 使用者嘗試上傳第 N 份資源 — Command"""

from behave import when


@when('使用者 "{email}" 嘗試上傳第 {n:d} 份資源')
def step_impl(context, email, n):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/pricing/check-upload",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
