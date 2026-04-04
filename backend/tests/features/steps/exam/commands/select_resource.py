"""When 使用者嘗試選擇資源 (@ignore) — Command"""

import uuid

from behave import when


@when('使用者 "{email}" 嘗試在測驗設定中選擇資源 {resource_id:d}')
def step_impl(context, email, resource_id):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    resource_uuid = str(uuid.UUID(int=resource_id))

    response = context.api_client.post(
        "/api/v1/exams/select-resource",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "resource_id": resource_uuid,
        },
    )
    context.last_response = response
