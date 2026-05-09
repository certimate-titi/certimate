"""Orphan Coach — Then: API 回應驗證步驟。

注意：
  - 「HTTP 狀態碼應為 {N}」使用 ecpay/readmodel_then/http_status.py 已定義的 step
  - 「操作失敗，狀態碼為 {N}」使用 common_then/failure_status_code.py 已定義的 step
"""

from behave import then


@then('回應應包含 conversation_id')
def step_has_conversation_id(context):
    data = context.last_response.json()
    assert "conversation_id" in data, f"回應缺少 conversation_id: {data}"
    assert data["conversation_id"], "conversation_id 不可為空"


@then('回應應包含 opening_message')
def step_has_opening_message(context):
    data = context.last_response.json()
    assert "opening_message" in data, f"回應缺少 opening_message: {data}"
    assert data["opening_message"], "opening_message 不可為空"


@then('回應應包含 assistant_reply')
def step_has_assistant_reply(context):
    data = context.last_response.json()
    assert "assistant_reply" in data, f"回應缺少 assistant_reply: {data}"


@then('回應應包含評分欄位（concept、reasoning、initiative、total）')
def step_has_scores(context):
    data = context.last_response.json()
    scores = data.get("scores", {})
    for field in ("concept", "reasoning", "initiative", "total"):
        assert field in scores, f"scores 缺少欄位 {field}: {scores}"


@then('回應的 status 應為「{status}」')
def step_response_status(context, status):
    data = context.last_response.json()
    actual = data.get("status")
    assert actual == status, f"status 期望 {status}，實際 {actual}"


@then('回應的 round_number 應為 {n:d}')
def step_round_number(context, n):
    data = context.last_response.json()
    actual = data.get("round_number")
    assert actual == n, f"round_number 期望 {n}，實際 {actual}"


@then('回應應包含 existing_conversation_id')
def step_has_existing_conversation_id(context):
    data = context.last_response.json()
    assert "existing_conversation_id" in data, f"回應缺少 existing_conversation_id: {data}"


@then('existing_conversation_id 不為 null')
def step_existing_conv_not_null(context):
    data = context.last_response.json()
    assert data.get("existing_conversation_id") is not None, (
        "existing_conversation_id 應不為 null"
    )


@then('existing_conversation_id 為 null')
def step_existing_conv_is_null(context):
    data = context.last_response.json()
    assert data.get("existing_conversation_id") is None, (
        f"existing_conversation_id 應為 null，實際: {data.get('existing_conversation_id')}"
    )


@then('回應應包含 messages 清單')
def step_has_messages_list(context):
    data = context.last_response.json()
    assert "messages" in data, f"回應缺少 messages: {data}"
    assert isinstance(data["messages"], list), "messages 應為陣列"


@then('mastery_committed 應為 {value}')
def step_mastery_committed(context, value):
    data = context.last_response.json()
    expected = value.lower() == "true"
    actual = data.get("mastery_committed")
    assert actual == expected, (
        f"mastery_committed 期望 {expected}，實際 {actual}"
    )


@then('回應應包含 paused 欄位')
def step_has_paused(context):
    data = context.last_response.json()
    assert "paused" in data, f"回應缺少 paused: {data}"


@then('對話應在 DB 中存在並為 socratic_orphan 模式')
def step_conversation_in_db(context):
    from app.models.ai_chat import AiChatSession
    import uuid
    conv_id = context.memo.get("conversation_id")
    assert conv_id, "conversation_id 未記錄"
    session = context.db_session.query(AiChatSession).filter(
        AiChatSession.id == uuid.UUID(conv_id)
    ).first()
    assert session is not None, f"對話 {conv_id} 在 DB 中不存在"
    assert session.mode == "socratic_orphan", f"mode 應為 socratic_orphan，實際: {session.mode}"


@then('model_used 應為 {model_name}')
def step_model_used(context, model_name):
    from app.models.ai_chat import AiChatSession
    import uuid
    conv_id = context.memo.get("conversation_id")
    session = context.db_session.query(AiChatSession).filter(
        AiChatSession.id == uuid.UUID(conv_id)
    ).first()
    assert session is not None, "對話不存在"
    assert session.model_used == model_name, (
        f"model_used 期望 {model_name}，實際 {session.model_used}"
    )
