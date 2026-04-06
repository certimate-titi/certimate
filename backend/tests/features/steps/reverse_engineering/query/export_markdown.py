"""When 匯出考科的知識樹為 Markdown — Query (GET)"""

from behave import when


@when('使用者 "{email}" 匯出考科 "{subject_name}" 的知識樹為 Markdown')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = context.ids.get(f"subject_name_{subject_name}")
    if not subject_id:
        raise KeyError(f"找不到考科 '{subject_name}'")

    response = context.api_client.get(
        f"/api/v1/reverse-engineering/subjects/{subject_id}/knowledge-tree/markdown",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
