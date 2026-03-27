"""When 使用者在教練對話框輸入訊息 — Command"""

import uuid

from behave import when


@when('使用者 "{email}" 在節點 {node_id:d} 的教練對話框輸入 "{message}"')
def step_impl(context, email, node_id, message):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    node_uuid = str(uuid.UUID(int=node_id))
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/knowledge-map/coach/message",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_id": node_uuid,
            "message": message,
        },
    )
    context.last_response = response
