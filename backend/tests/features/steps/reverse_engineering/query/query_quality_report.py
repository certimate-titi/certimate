"""When 查詢逆向工程品質報告 — Query (GET)"""

from behave import when


@when('管理員 "{email}" 查詢逆向工程品質報告')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # Use the subject from context
    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = val
            break
    if not subject_id:
        raise KeyError("找不到任何考科")

    response = context.api_client.get(
        f"/api/v1/reverse-engineering/subjects/{subject_id}/quality-report",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
