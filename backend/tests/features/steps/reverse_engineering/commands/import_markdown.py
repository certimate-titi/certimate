"""When 管理員匯入 Markdown 知識結構 — Command (POST)"""

from behave import when


@when('管理員 "{email}" 匯入以下 Markdown 知識結構到考科 "{subject_name}"：')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = context.ids.get(f"subject_name_{subject_name}")
    if not subject_id:
        raise KeyError(f"找不到考科 '{subject_name}'")

    markdown_content = context.text

    response = context.api_client.post(
        f"/api/v1/reverse-engineering/subjects/{subject_id}/import-markdown",
        headers={"Authorization": f"Bearer {token}"},
        json={"markdown": markdown_content},
    )
    context.last_response = response
