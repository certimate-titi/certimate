"""When 管理員查詢合併衝突清單 — Query"""

from behave import when


@when('管理員 "{email}" 查詢合併衝突清單')
def step_query_conflicts(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = context.memo.get("merge_subject_id")
    assert subject_id, "找不到 merge_subject_id"

    response = context.api_client.get(
        f"/api/v1/knowledge-merge/subjects/{subject_id}/conflicts",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
