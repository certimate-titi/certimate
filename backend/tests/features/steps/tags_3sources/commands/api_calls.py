"""API calls — Feature 54 Tags 3 Sources BDD."""

from behave import when


@when('alice POST /api/v1/chat-annotations 含 user_annotation "{user_annotation}" 和 highlighted_text "{highlighted_text}"')
def step_alice_post_annotation(context, user_annotation, highlighted_text):
    token = context.jwt_helper.generate(context.ids["alice@example.com"])
    session_id = context.memo["session_id"]
    message_id = context.memo["message_id"]
    resp = context.api_client.post(
        "/api/v1/chat-annotations",
        json={
            "session_id": session_id,
            "message_id": message_id,
            "highlighted_text": highlighted_text,
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


@when('alice PATCH /api/v1/chat-annotations/{annotation_id} 更新 user_annotation 為 "{user_annotation}"')
def step_alice_patch_annotation(context, annotation_id, user_annotation):
    token = context.jwt_helper.generate(context.ids["alice@example.com"])
    ann_id = context.memo.get("annotation_id", annotation_id)
    resp = context.api_client.patch(
        f"/api/v1/chat-annotations/{ann_id}",
        json={"user_annotation": user_annotation},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice DELETE /api/v1/chat-annotations/{annotation_id}')
def step_alice_delete_annotation(context, annotation_id):
    token = context.jwt_helper.generate(context.ids["alice@example.com"])
    ann_id = context.memo.get("annotation_id", annotation_id)
    resp = context.api_client.delete(
        f"/api/v1/chat-annotations/{ann_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice PATCH /api/v1/knowledge-map/scaffolds/{scaffold_id} 更新 user_response 為 "{user_response}"')
def step_alice_patch_scaffold_response(context, scaffold_id, user_response):
    token = context.jwt_helper.generate(context.ids["alice@example.com"])
    sc_id = context.memo.get("scaffold_id", scaffold_id)
    resp = context.api_client.patch(
        f"/api/v1/knowledge-map/scaffolds/{sc_id}",
        json={"user_response": user_response},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice GET /api/v1/user-tags/aggregate')
def step_alice_get_aggregate(context):
    token = context.jwt_helper.generate(context.ids["alice@example.com"])
    resp = context.api_client.get(
        "/api/v1/user-tags/aggregate",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice GET /api/v1/user-tags/aggregate?subject_id={subject_id}')
def step_alice_get_aggregate_with_subject(context, subject_id):
    token = context.jwt_helper.generate(context.ids["alice@example.com"])
    actual_subject_id = context.memo.get("subject_id", subject_id)
    resp = context.api_client.get(
        f"/api/v1/user-tags/aggregate?subject_id={actual_subject_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('bob GET /api/v1/user-tags/aggregate')
def step_bob_get_aggregate(context):
    token = context.jwt_helper.generate(context.ids["bob@example.com"])
    resp = context.api_client.get(
        "/api/v1/user-tags/aggregate",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice GET /api/v1/user-tags/items?tag=ai')
def step_alice_get_items_tag_ai(context):
    token = context.jwt_helper.generate(context.ids["alice@example.com"])
    resp = context.api_client.get(
        "/api/v1/user-tags/items?tag=ai",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp


@when('alice GET /api/v1/user-notes/export/obsidian?force=true')
def step_alice_get_export_obsidian(context):
    token = context.jwt_helper.generate(context.ids["alice@example.com"])
    resp = context.api_client.get(
        "/api/v1/user-notes/export/obsidian?force=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = resp
