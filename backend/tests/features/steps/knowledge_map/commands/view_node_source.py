"""When 使用者查看節點的溯源內容 — Query"""

import uuid

from behave import when


@when('使用者 "{email}" 查看節點 {node_id:d} 的溯源內容')
def step_impl(context, email, node_id):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    node_uuid = str(uuid.UUID(int=node_id))
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/knowledge-map/nodes/{node_uuid}/source",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
