"""When 使用者 "..." 再次提交主旨為 "..." 的意見反饋 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 再次提交主旨為 "{subject}" 的意見反饋')
def step_impl(context, email, subject):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "BUG",
            "subject": subject,
            "content": "重複提交測試內容",
        },
    )
    context.last_response = response
