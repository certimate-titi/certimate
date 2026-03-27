"""When 使用者提交測驗設定（選擇單一節點）— Command"""

import uuid

from behave import when


@when('使用者 "{email}" 提交測驗設定，選擇節點 {node_id:d}，題數為 {count:d}')
def step_impl(context, email, node_id, count):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    node_uuid = str(uuid.UUID(int=node_id))

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": [node_uuid],
            "question_count": count,
        },
    )
    context.last_response = response
