"""When 使用者查詢節點錯題明細 — Query"""

from behave import when


@when('使用者 "{email}" 查詢節點 "{node_name}" 的錯題明細')
def step_impl(context, email, node_name):
    user_id = context.ids[email]
    node_id = context.ids[f"node_{node_name}"]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/wrong-answer-map/nodes/{node_id}/wrong-answers",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
