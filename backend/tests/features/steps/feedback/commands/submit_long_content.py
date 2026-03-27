"""When 使用者 "..." 提交意見反饋，內容長度為 N 個字元 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 提交意見反饋，內容長度為 {length:d} 個字元')
def step_impl(context, email, length):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "BUG",
            "subject": "測試主旨",
            "content": "A" * length,
        },
    )
    context.last_response = response
