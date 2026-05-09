"""Orphan Coach — When: API 呼叫步驟（LLM 以 mock 取代）。"""

from unittest.mock import patch, MagicMock

from behave import when


def _get_token(context) -> str:
    """取得測試用 JWT token。"""
    email = context.memo.get("current_user_email")
    if email:
        return context.jwt_helper.generate_token(context.ids[email])
    # fallback：取第一個使用者
    first_email = next(iter(context.ids), None)
    if first_email:
        return context.jwt_helper.generate_token(context.ids[first_email])
    return ""


def _make_mock_anthropic():
    """建立 mock Anthropic client（回傳固定引導問句 + 評分）。"""
    mock_client = MagicMock()
    # 模擬 messages.create 回傳
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="你對網路安全有什麼初步的印象？從你學過的哪些概念出發？")]
    mock_client.messages.create.return_value = mock_response
    return mock_client


def _make_mock_evaluator_response(concept=0.5, reasoning=0.5):
    """建立 mock 評分回應。"""
    import json
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(
        text=json.dumps({"concept": concept, "reasoning": reasoning, "rationale": "測試評分"})
    )]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@when('我啟動節點「{node_name}」的蘇格拉底對話')
def step_start_conversation(context, node_name):
    node_id = context.memo.get("node_id")
    token = _get_token(context)
    mock_client = _make_mock_anthropic()
    with patch("app.services.orphan_coach_service._get_anthropic", return_value=mock_client):
        context.last_response = context.api_client.post(
            "/api/v1/orphan-coach/conversations",
            json={"node_id": node_id},
            headers={"Authorization": f"Bearer {token}"},
        )
    if context.last_response.status_code == 201:
        data = context.last_response.json()
        context.memo["conversation_id"] = data.get("conversation_id")


@when('我啟動一個不存在節點（UUID 隨機）的蘇格拉底對話')
def step_start_conversation_nonexistent_node(context):
    import uuid
    token = _get_token(context)
    mock_client = _make_mock_anthropic()
    with patch("app.services.orphan_coach_service._get_anthropic", return_value=mock_client):
        context.last_response = context.api_client.post(
            "/api/v1/orphan-coach/conversations",
            json={"node_id": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )


@when('我向蘇格拉底對話發送訊息「{text}」')
def step_send_message(context, text):
    conv_id = context.memo.get("conversation_id")
    token = _get_token(context)
    mock_client = _make_mock_anthropic()
    with patch("app.services.orphan_coach_service._get_anthropic", return_value=mock_client):
        context.last_response = context.api_client.post(
            f"/api/v1/orphan-coach/conversations/{conv_id}/messages",
            json={"text": text},
            headers={"Authorization": f"Bearer {token}"},
        )
    if context.last_response.status_code == 200:
        data = context.last_response.json()
        context.memo["last_message_response"] = data


@when('我發送空訊息到蘇格拉底對話')
def step_send_empty_message(context):
    conv_id = context.memo.get("conversation_id")
    token = _get_token(context)
    context.last_response = context.api_client.post(
        f"/api/v1/orphan-coach/conversations/{conv_id}/messages",
        json={"text": ""},
        headers={"Authorization": f"Bearer {token}"},
    )


@when('我查詢蘇格拉底對話詳情')
def step_get_conversation(context):
    conv_id = context.memo.get("conversation_id")
    token = _get_token(context)
    context.last_response = context.api_client.get(
        f"/api/v1/orphan-coach/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('我查詢節點的進行中對話')
def step_find_active_conversation(context):
    node_id = context.memo.get("node_id")
    token = _get_token(context)
    context.last_response = context.api_client.get(
        f"/api/v1/orphan-coach/conversations?node_id={node_id}",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('我暫停蘇格拉底對話')
def step_pause_conversation(context):
    conv_id = context.memo.get("conversation_id")
    token = _get_token(context)
    context.last_response = context.api_client.post(
        f"/api/v1/orphan-coach/conversations/{conv_id}/pause",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('我以其他使用者身分查詢此蘇格拉底對話')
def step_get_conversation_other_user(context):
    conv_id = context.memo.get("conversation_id")
    # 用第二個使用者 token
    emails = list(context.ids.keys())
    other_email = emails[1] if len(emails) > 1 else emails[0]
    token = context.jwt_helper.generate_token(context.ids[other_email])
    context.last_response = context.api_client.get(
        f"/api/v1/orphan-coach/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
