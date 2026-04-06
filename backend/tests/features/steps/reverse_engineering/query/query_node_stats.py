"""When 查詢知識節點的題目統計 — Query (GET)"""

from behave import when


@when('管理員 "{email}" 查詢知識節點 "{node_name}" 的題目統計')
def step_impl(context, email, node_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    node_id = context.ids.get(f"node_{node_name}")
    if not node_id:
        raise KeyError(f"找不到知識節點 '{node_name}'")

    response = context.api_client.get(
        f"/api/v1/reverse-engineering/nodes/{node_id}/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
