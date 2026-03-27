"""When 使用者 "..." 查看反饋 "..." 的詳細資訊 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看反饋 "{feedback_id}" 的詳細資訊')
def step_impl(context, email, feedback_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/feedback/{feedback_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
