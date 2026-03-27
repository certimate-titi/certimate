"""When 使用者 "{email}" 點擊右側 25% 心智圖導覽區上的知識點 "{node_name}" — Query"""

from behave import when


@when('使用者 "{email}" 點擊右側 25% 心智圖導覽區上的知識點 "{node_name}"')
def click_knowledge_node(context, email, node_name):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    node_key = f"node_{node_name}"
    if node_key not in context.ids:
        raise KeyError(f"找不到知識節點 '{node_name}' 的 ID（key: {node_key}）")

    user_id = context.ids[email]
    node_id = context.ids[node_key]
    token = context.jwt_helper.generate_token(user_id)

    context.memo["current_token"] = token
    context.memo["target_node_id"] = node_id

    response = context.api_client.get(
        f"/api/v1/knowledge-map/nodes/{node_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
