"""When 使用者刪除資源 — Command (DELETE)"""

import uuid

from behave import when


@when('使用者 "{email}" 刪除資源 {resource_id:d}')
def step_impl(context, email, resource_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    res_uuid = uuid.UUID(int=resource_id)

    response = context.api_client.delete(
        f"/api/v1/resource-library/{res_uuid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
