"""When 系統更新使用者的節點掌握度 — Command"""

from behave import when


@when('系統更新使用者 "{email}" 的節點掌握度')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = val
            break

    response = context.api_client.post(
        f"/api/v1/wrong-answer-map/subjects/{subject_id}/update-mastery",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
