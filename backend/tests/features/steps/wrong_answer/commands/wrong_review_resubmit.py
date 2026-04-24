"""When 錯題複習重新作答 N 題 — 透過 /practice/submit 模擬重考。"""

from behave import when

from app.models.question import Question


@when('使用者 "{email}" 在錯題複習中重新作答 {keyword} 相關 {total:d} 題，答對 {correct:d} 題')
def step_wrong_review_resubmit(context, email, keyword, total, correct):
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(user_id)

    # 以 keyword 對應的節點題目為主；不足時以任一可用題目補齊
    db = context.db_session
    node_key = next(
        (k for k in context.ids if k.startswith("node_") and keyword in k and not k.endswith("_parent")),
        None,
    )
    assert node_key, f"找不到節點含 keyword '{keyword}'"
    question_id = context.ids.get(f"question_{node_key[len('node_'):]}")
    assert question_id, "找不到練習題"

    q = db.query(Question).filter(Question.id == question_id).first()
    correct_ans = q.correct_answer
    wrong_ans = "A" if correct_ans != "A" else "C"

    for i in range(total):
        answer = correct_ans if i < correct else wrong_ans
        resp = context.api_client.post(
            "/api/v1/practice/submit",
            headers={"Authorization": f"Bearer {token}"},
            json={"question_id": question_id, "selected_answer": answer},
        )
        context.last_response = resp

    # 重新抓錯題地圖，讓後續 Then 能驗證節點 mastery/color
    from app.models.knowledge_node import KnowledgeNode
    node = db.query(KnowledgeNode).filter(KnowledgeNode.id == q.node_id).first()
    subject_id = str(node.subject_id) if node and node.subject_id else None
    if subject_id:
        context.last_response = context.api_client.get(
            f"/api/v1/wrong-answer-map/subjects/{subject_id}/map",
            headers={"Authorization": f"Bearer {token}"},
        )
