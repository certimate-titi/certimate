"""When 使用者重新解析資源 — Command (POST)"""

import uuid

from behave import when


@when('使用者 "{email}" 重新解析資源 {resource_id:d}')
def step_impl(context, email, resource_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    res_uuid = uuid.UUID(int=resource_id)

    response = context.api_client.post(
        f"/api/v1/resource-library/{res_uuid}/reparse",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
