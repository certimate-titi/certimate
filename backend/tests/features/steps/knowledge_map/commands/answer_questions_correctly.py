"""When 使用者在模擬考中連續答對該節點衍伸出的 {count} 道難題 — Command"""

from behave import when


@when('使用者在模擬考中連續答對該節點衍伸出的 {count:d} 道難題')
def answer_questions_correctly(context, count):
    node_id = context.memo.get("target_node_id")
    if not node_id:
        raise KeyError("需要先設定 target_node_id（透過 Given 節點初始狀態步驟）")

    token = context.memo.get("current_token")
    if not token:
        raise KeyError("需要先登入（current_token 不存在）")

    payload = {
        "correct_count": count,
        "total_count": count,
    }

    response = context.api_client.post(
        f"/api/v1/knowledge-map/nodes/{node_id}/submit-answers",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
