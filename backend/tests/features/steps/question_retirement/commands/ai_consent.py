"""When 使用者同意/拒絕 AI 出題條款 — Command"""

from behave import when


@when('使用者發起 AI 出題')
def step_initiate(context):
    email = context.memo.get("ai_consent_email")
    user_id = context.ids.get(email)
    token = context.jwt_helper.generate_token(user_id) if user_id else None

    response = context.api_client.post(
        "/api/v1/ai-questions/generate",
        headers={"Authorization": f"Bearer {token}"} if token else {},
        json={},
    )
    context.last_response = response


@when('使用者同意 AI 出題條款')
def step_consent(context):
    email = context.memo.get("ai_consent_email")
    user_id = context.ids.get(email)
    token = context.jwt_helper.generate_token(user_id) if user_id else None

    response = context.api_client.post(
        "/api/v1/ai-questions/consent",
        headers={"Authorization": f"Bearer {token}"} if token else {},
        json={"agreed": True},
    )
    context.last_response = response


@when('使用者拒絕 AI 出題條款')
def step_reject(context):
    email = context.memo.get("ai_consent_email")
    user_id = context.ids.get(email)
    token = context.jwt_helper.generate_token(user_id) if user_id else None

    response = context.api_client.post(
        "/api/v1/ai-questions/consent",
        headers={"Authorization": f"Bearer {token}"} if token else {},
        json={"agreed": False},
    )
    context.last_response = response
