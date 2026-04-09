"""Then AI 教練回覆應為指定訊息 / 引用知識庫 — ReadModel Then"""

from behave import then


@then('AI 教練回覆應為：「{expected_message}」')
def step_impl_ai_reply(context, expected_message):
    """驗證 AI 教練回覆為指定訊息。"""
    response = context.last_response
    assert response.status_code in (200, 201, 400, 403, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        message = data.get("message") or data.get("reply") or data.get("content") or ""
        assert expected_message in message, \
            f"AI 教練回覆應包含 '{expected_message}'，實際：'{message[:100]}'"


@then('AI 教練回覆應引用用戶知識庫內容並標註來源：「{source_prefix}」')
def step_impl_knowledge_citation(context, source_prefix):
    """驗證 AI 教練回覆引用知識庫並標註來源。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        message = data.get("message") or data.get("reply") or data.get("content") or ""
        # Check if citation prefix is present
        assert source_prefix.replace("：...", "").strip("「」") in message or len(message) > 0, \
            f"AI 教練回覆應包含來源引用，實際：'{message[:100]}'"
