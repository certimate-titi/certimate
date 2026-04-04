"""When 使用者提交測驗設定，選擇知識節點名稱 — Command"""

from behave import when


@when('使用者 "{email}" 提交測驗設定，選擇知識節點 "{node_name}"，題數為 {count:d}')
def step_impl(context, email, node_name, count):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    node_key = f"node_{node_name}"
    if node_key not in context.ids:
        raise KeyError(f"找不到節點 '{node_name}' 的 ID")

    node_uuid = context.ids[node_key]

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": [node_uuid],
            "question_count": count,
        },
    )
    context.last_response = response
