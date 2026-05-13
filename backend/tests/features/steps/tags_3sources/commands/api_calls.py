"""API calls — Feature 54 Tags 3 Sources BDD."""

from behave import when


def _token(context, email: str) -> str:
    return context.jwt_helper.generate_token(context.ids[email])


@when('alice POST /api/v1/chat-annotations with annotation text "{user_annotation}"')
def step_alice_post_annotation_f54(context, user_annotation):
    token = _token(context, "alice@example.com")
    session_id = context.memo["session_id"]
    message_id = context.memo["message_id"]
    resp = context.api_client.post(
        "/api/v1/chat-annotations",
        json={
            "session_id": session_id,
            "message_id": message_id,
            "highlighted_text": "重要片段",
            "user_annotation": user_annotation,
            "annotation_type": "note",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp
    if resp.status_code == 201:
        data = resp.json()
        ann = data.get("annotation", data)
        context.memo["annotation_id"] = ann.get("id", context.memo.get("annotation_id"))


@when('alice 更新 annotation user_annotation 為 "{user_annotation}"')
def step_alice_patch_annotation_f54(context, user_annotation):
    token = _token(context, "alice@example.com")
    ann_id = context.memo["annotation_id"]
    resp = context.api_client.patch(
        f"/api/v1/chat-annotations/{ann_id}",
        json={"user_annotation": user_annotation},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice 刪除 memo["annotation_id"] 的 annotation')
def step_alice_delete_annotation_f54(context):
    token = _token(context, "alice@example.com")
    ann_id = context.memo["annotation_id"]
    resp = context.api_client.delete(
        f"/api/v1/chat-annotations/{ann_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice 更新 scaffold user_response 為 "{user_response}" via API')
def step_alice_patch_scaffold_response_f54(context, user_response):
    token = _token(context, "alice@example.com")
    sc_id = context.memo["scaffold_id"]
    resp = context.api_client.patch(
        f"/api/v1/knowledge-map/scaffolds/{sc_id}",
        json={"user_response": user_response},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice GET /api/v1/user-tags/aggregate')
def step_alice_get_aggregate(context):
    token = _token(context, "alice@example.com")
    resp = context.api_client.get(
        "/api/v1/user-tags/aggregate",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice GET /api/v1/user-tags/aggregate?subject_id={subject_id}')
def step_alice_get_aggregate_with_subject(context, subject_id):
    token = _token(context, "alice@example.com")
    actual_subject_id = context.memo.get("subject_id", subject_id)
    resp = context.api_client.get(
        f"/api/v1/user-tags/aggregate?subject_id={actual_subject_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('bob GET /api/v1/user-tags/aggregate')
def step_bob_get_aggregate(context):
    token = _token(context, "bob@example.com")
    resp = context.api_client.get(
        "/api/v1/user-tags/aggregate",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice GET /api/v1/user-tags/items?tag=ai')
def step_alice_get_items_tag_ai(context):
    token = _token(context, "alice@example.com")
    resp = context.api_client.get(
        "/api/v1/user-tags/items?tag=ai",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


# Note: alice GET /api/v1/user-notes/export/obsidian?force=true 已在 obsidian_export steps 定義
