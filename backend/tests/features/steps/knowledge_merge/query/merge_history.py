"""When 管理員查詢合併歷史 — Query"""

from behave import when


@when('管理員 "{email}" 查詢考科 "{subject_name}" 的合併歷史')
def step_query_merge_history(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = context.ids.get(f"subject_name_{subject_name}")
    assert subject_id, f"找不到考科 '{subject_name}'"

    response = context.api_client.get(
        f"/api/v1/knowledge-merge/subjects/{subject_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
