"""When 使用者匯出錯題地圖為 Markdown — Query"""

from behave import when


@when('使用者 "{email}" 匯出考科 "{subject_name}" 的錯題地圖為 Markdown')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    subject_id = context.ids.get(f"subject_name_{subject_name}")
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/wrong-answer-map/subjects/{subject_id}/map/markdown",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
