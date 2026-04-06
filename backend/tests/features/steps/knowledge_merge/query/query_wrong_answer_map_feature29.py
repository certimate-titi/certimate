"""When 使用者查詢錯題地圖（Feature 27）— Query (Feature 29 downstream)"""

from behave import when


@when('使用者 "{email}" 查詢錯題地圖（Feature 27）')
def step_query_wrong_answer_map(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = context.memo.get("merge_subject_id")
    assert subject_id, "找不到 merge_subject_id"

    response = context.api_client.get(
        f"/api/v1/wrong-answer-map/subjects/{subject_id}/map",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
