"""When 查詢節點詳細資訊 — Query"""

from behave import when


@when('查詢節點 "{name}" 的詳細資訊')
def step_query_node_detail(context, name):
    node_id = context.ids.get(f"node_{name}")
    assert node_id, f"找不到節點 '{name}'"

    # Use first available user for auth
    admin_email = None
    for key in context.ids:
        if "@" in key:
            admin_email = key
            break

    user_id = context.ids[admin_email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/knowledge-merge/nodes/{node_id}/detail",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
