"""When 練習模式操作。"""

import uuid

from behave import when


@when('使用者 "{email}" 查詢節點 "{node_name}" 的練習題')
def step_query_node_questions(context, email, node_name):
    """查詢知識節點下的練習題列表。"""
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    # 從 context.ids 找到節點 ID
    node_id = None
    from app.models.knowledge_node import KnowledgeNode
    for key, val in context.ids.items():
        if key.startswith("node_"):
            node = context.db_session.query(KnowledgeNode).filter(
                KnowledgeNode.id == uuid.UUID(val),
                KnowledgeNode.name == node_name,
            ).first()
            if node:
                node_id = str(node.id)
                break

    assert node_id, f"找不到知識節點 {node_name}"

    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        f"/api/v1/practice/nodes/{node_id}/questions",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 練習作答題目 "{q_key}"，選擇 "{answer}"')
def step_submit_practice(context, email, q_key, answer):
    """提交練習作答。"""
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    question_id = context.ids.get(f"question_{q_key}")
    assert question_id, f"找不到題目 {q_key}"

    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.post(
        "/api/v1/practice/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_id": question_id,
            "selected_answer": answer,
        },
    )
    context.last_response = response


@when('使用者 "{email}" 練習作答不存在的題目')
def step_submit_nonexistent(context, email):
    """提交不存在的題目作答。"""
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    fake_id = str(uuid.uuid4())
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.post(
        "/api/v1/practice/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_id": fake_id,
            "selected_answer": "A",
        },
    )
    context.last_response = response
