"""When 練習模式答對題目 — Epic 3 Node Mastery Pipeline."""

from behave import when


@when('使用者在練習模式回答 "{node_name}" 的題目並答對')
def step_practice_answer_correctly(context, node_name):
    """以正解提交練習題（correct_answer="B"）。"""
    email = context.memo.get("practice_email")
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    question_id = context.ids.get(f"question_{node_name}")
    assert question_id, f"找不到節點 {node_name} 的練習題"

    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.post(
        "/api/v1/practice/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={"question_id": question_id, "selected_answer": "B"},
    )
    context.last_response = response
