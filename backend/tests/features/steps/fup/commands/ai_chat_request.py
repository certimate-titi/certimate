"""When — 使用者發起 AI 對話。"""

from behave import when


@when('使用者 "{email}" 發起第 {n:d} 次 AI 對話')
def step_ai_chat_request(context, email, n):
    token = context.jwt_helper.generate_token(context.ids.get(email, email))
    context.last_response = context.api_client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": f"Test AI chat request #{n}", "context_type": "knowledge_node", "context_id": "00000000-0000-0000-0000-000000000000"},
    )
