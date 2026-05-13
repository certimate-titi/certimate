"""When step API calls — Feature 50 User Notes BDD."""

import uuid

from behave import when


def _token(context, email: str) -> str:
    return context.jwt_helper.generate_token(context.ids[email])


# ── POST /api/v1/user-notes ───────────────────────────────────────────────────

@when('alice POST /api/v1/user-notes 含 subject_id 和 content "{content}"')
def step_alice_create_note_no_node(context, content):
    subject_id = context.memo["subject_id"]
    token = _token(context, "alice@example.com")

    payload = {
        "subject_id": subject_id,
        "content": content,
    }
    context.last_response = context.api_client.post(
        "/api/v1/user-notes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 201:
        data = context.last_response.json()
        context.memo["created_note"] = data
        context.memo["note_id"] = data.get("id")


@when('alice POST /api/v1/user-notes 含 subject_id、node_id 和 content "{content}"')
def step_alice_create_note_with_node(context, content):
    subject_id = context.memo["subject_id"]
    node_id = context.memo["node_id"]
    token = _token(context, "alice@example.com")

    payload = {
        "subject_id": subject_id,
        "node_id": node_id,
        "content": content,
    }
    context.last_response = context.api_client.post(
        "/api/v1/user-notes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 201:
        data = context.last_response.json()
        context.memo["created_note"] = data
        context.memo["note_id"] = data.get("id")


@when('alice POST /api/v1/user-notes 含不存在的 subject_id 和 content "{content}"')
def step_alice_create_note_invalid_subject(context, content):
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.post(
        "/api/v1/user-notes",
        json={
            "subject_id": str(uuid.uuid4()),  # 不存在的 subject
            "content": content,
        },
        headers={"Authorization": f"Bearer {token}"},
    )


# ── GET /api/v1/user-notes ────────────────────────────────────────────────────

@when('alice GET /api/v1/user-notes')
def step_alice_list_notes(context):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.get(
        "/api/v1/user-notes",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["list_response"] = context.last_response.json()


@when('alice GET /api/v1/user-notes?subject_id=<subject_id>')
def step_alice_list_notes_by_subject(context):
    token = _token(context, "alice@example.com")
    subject_id = context.memo["subject_id"]
    context.last_response = context.api_client.get(
        f"/api/v1/user-notes?subject_id={subject_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["filtered_list_response"] = context.last_response.json()


@when('bob GET /api/v1/user-notes')
def step_bob_list_notes(context):
    token = _token(context, "bob@example.com")
    context.last_response = context.api_client.get(
        "/api/v1/user-notes",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["bob_list_response"] = context.last_response.json()


# ── PATCH /api/v1/user-notes/{id} ────────────────────────────────────────────

@when('alice PATCH /api/v1/user-notes/<note_id> 含 content "{content}"')
def step_alice_update_note(context, content):
    note_id = context.memo["note_id"]
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.patch(
        f"/api/v1/user-notes/{note_id}",
        json={"content": content},
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["updated_note"] = context.last_response.json()


@when('bob PATCH /api/v1/user-notes/<alice_note_id> 含 content "{content}"')
def step_bob_update_alice_note(context, content):
    note_id = context.memo["alice_note_id"]
    token = _token(context, "bob@example.com")

    context.last_response = context.api_client.patch(
        f"/api/v1/user-notes/{note_id}",
        json={"content": content},
        headers={"Authorization": f"Bearer {token}"},
    )


@when('alice PATCH /api/v1/user-notes/<nonexistent_id> 含 content "{content}"')
def step_alice_update_nonexistent_note(context, content):
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.patch(
        f"/api/v1/user-notes/{uuid.uuid4()}",
        json={"content": content},
        headers={"Authorization": f"Bearer {token}"},
    )


# ── DELETE /api/v1/user-notes/{id} ───────────────────────────────────────────

@when('alice DELETE /api/v1/user-notes/<note_id>')
def step_alice_delete_note(context):
    note_id = context.memo["note_id"]
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.delete(
        f"/api/v1/user-notes/{note_id}",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('bob DELETE /api/v1/user-notes/<alice_note_id>')
def step_bob_delete_alice_note(context):
    note_id = context.memo["alice_note_id"]
    token = _token(context, "bob@example.com")

    context.last_response = context.api_client.delete(
        f"/api/v1/user-notes/{note_id}",
        headers={"Authorization": f"Bearer {token}"},
    )


# ── PATCH /api/v1/chat-annotations/{id} ──────────────────────────────────────

@when('alice PATCH /api/v1/chat-annotations/<annotation_id> 含 user_annotation "{annotation}"')
def step_alice_patch_annotation(context, annotation):
    annotation_id = context.memo["annotation_id"]
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.patch(
        f"/api/v1/chat-annotations/{annotation_id}",
        json={"user_annotation": annotation},
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["updated_annotation"] = context.last_response.json()


# ── PATCH /api/v1/knowledge-map/scaffolds/{id} ───────────────────────────────

@when('alice PATCH /api/v1/knowledge-map/scaffolds/<scaffold_id> 含 user_response "{response}"')
def step_alice_patch_scaffold(context, response):
    scaffold_id = context.memo["scaffold_id"]
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.patch(
        f"/api/v1/knowledge-map/scaffolds/{scaffold_id}",
        json={"user_response": response},
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["scaffold_patch_response"] = context.last_response.json()


@when('bob PATCH /api/v1/knowledge-map/scaffolds/<scaffold_id> 含 user_response "{response}"')
def step_bob_patch_scaffold(context, response):
    scaffold_id = context.memo["scaffold_id"]
    token = _token(context, "bob@example.com")

    context.last_response = context.api_client.patch(
        f"/api/v1/knowledge-map/scaffolds/{scaffold_id}",
        json={"user_response": response},
        headers={"Authorization": f"Bearer {token}"},
    )
