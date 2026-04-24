"""When 使用者查詢節點的學習鷹架（TASK-02）— Command"""

import uuid

from behave import when


@when('使用者 "{email}" 查詢節點 {node_id:d} 的學習鷹架')
def step_impl(context, email, node_id):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    node_uuid = str(uuid.UUID(int=node_id))
    token = context.jwt_helper.generate_token(user_id)

    context.last_response = context.api_client.get(
        f"/api/v1/knowledge-map/nodes/{node_uuid}/scaffolds",
        headers={"Authorization": f"Bearer {token}"},
    )
