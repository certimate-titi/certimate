"""When step API calls — Feature 49 Chat Annotations BDD."""

import uuid

from behave import when


def _token(context, email: str) -> str:
    return context.jwt_helper.generate_token(context.ids[email])


@when('alice POST /api/v1/chat-annotations 含 highlighted_text 與 user_annotation "{annotation}"')
def step_alice_create_annotation_happy(context, annotation):
    session_id = context.memo["session_id"]
    message_id = context.memo["message_id"]
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.post(
        "/api/v1/chat-annotations",
        json={
            "message_id": message_id,
            "session_id": session_id,
            "highlighted_text": "AI 回應中的重要片段",
            "user_annotation": annotation,
            "annotation_type": "note",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 201:
        data = context.last_response.json()
        context.memo["created_annotation"] = data
        context.memo["annotation_id"] = data.get("id")


@when('alice POST /api/v1/chat-annotations 含 user_annotation "{annotation}"')
def step_alice_create_annotation_short(context, annotation):
    session_id = context.memo["session_id"]
    message_id = context.memo["message_id"]
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.post(
        "/api/v1/chat-annotations",
        json={
            "message_id": message_id,
            "session_id": session_id,
            "highlighted_text": "片段",
            "user_annotation": annotation,
            "annotation_type": "note",
        },
        headers={"Authorization": f"Bearer {token}"},
    )


@when('bob POST /api/v1/chat-annotations 用 alice 的 session_id')
def step_bob_create_annotation_cross_user(context):
    session_id = context.memo["alice_session_id"]
    message_id = context.memo["message_id"]
    token = _token(context, "bob@example.com")

    context.last_response = context.api_client.post(
        "/api/v1/chat-annotations",
        json={
            "message_id": message_id,
            "session_id": session_id,
            "highlighted_text": "嘗試標記他人對話",
            "user_annotation": "這是 bob 嘗試標記 alice 的對話，應被拒絕並回傳 403",
            "annotation_type": "note",
        },
        headers={"Authorization": f"Bearer {token}"},
    )


@when('alice POST /api/v1/chat-annotations 第 6 筆')
def step_alice_create_annotation_6th(context):
    session_id = context.memo["session_id"]
    message_id = context.memo["message_id"]
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.post(
        "/api/v1/chat-annotations",
        json={
            "message_id": message_id,
            "session_id": session_id,
            "highlighted_text": "第六筆標記片段",
            "user_annotation": "這是第六筆評語，應該要被拒絕並回傳 409 上限錯誤",
            "annotation_type": "note",
        },
        headers={"Authorization": f"Bearer {token}"},
    )


@when('alice GET /api/v1/chat-annotations')
def step_alice_list_annotations(context):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.get(
        "/api/v1/chat-annotations",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["list_response"] = context.last_response.json()


@when('alice GET /api/v1/chat-annotations?session_id=<session_1_id>')
def step_alice_list_annotations_filter_session1(context):
    token = _token(context, "alice@example.com")
    session_1_id = context.memo["session_1_id"]
    context.last_response = context.api_client.get(
        f"/api/v1/chat-annotations?session_id={session_1_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["filtered_list_response"] = context.last_response.json()


@when('alice DELETE /api/v1/chat-annotations/<annotation_id>')
def step_alice_delete_annotation(context):
    annotation_id = context.memo["annotation_id"]
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.delete(
        f"/api/v1/chat-annotations/{annotation_id}",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('bob DELETE /api/v1/chat-annotations/<alice_annotation_id>')
def step_bob_delete_alice_annotation(context):
    annotation_id = context.memo["alice_annotation_id"]
    token = _token(context, "bob@example.com")
    context.last_response = context.api_client.delete(
        f"/api/v1/chat-annotations/{annotation_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
