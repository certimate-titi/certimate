"""When 使用者 "{email}" 在對話框輸入：「{message}」 — Command"""

from behave import when


@when('使用者 "{email}" 在對話框輸入：「{message}」')
def ai_coach_input(context, email, message):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    payload = {
        "message": message,
    }

    response = context.api_client.post(
        "/api/v1/knowledge-map/ai-coach/chat",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
