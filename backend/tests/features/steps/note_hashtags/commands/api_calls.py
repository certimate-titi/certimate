"""When step API calls — Feature 52 筆記 hashtag 系統 BDD."""

import uuid

from behave import when


def _token(context, email: str) -> str:
    return context.jwt_helper.generate_token(context.ids[email])


# ── POST /api/v1/user-notes ───────────────────────────────────────────────────

@when('alice POST /api/v1/user-notes 含 content "{content}"')
def step_alice_create_note_with_content(context, content):
    subject_id = context.memo["subject_id"]
    token = _token(context, "alice@example.com")

    context.last_response = context.api_client.post(
        "/api/v1/user-notes",
        json={
            "subject_id": subject_id,
            "content": content,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 201:
        data = context.last_response.json()
        context.memo["created_note"] = data
        context.memo["note_id"] = data.get("id")


# ── GET /api/v1/user-notes/tags ───────────────────────────────────────────────

@when('alice GET /api/v1/user-notes/tags')
def step_alice_list_tags(context):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.get(
        "/api/v1/user-notes/tags",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["tags_response"] = context.last_response.json()


@when('alice GET /api/v1/user-notes/tags?subject_id=<subject_id>')
def step_alice_list_tags_by_subject(context):
    token = _token(context, "alice@example.com")
    subject_id = context.memo["subject_id"]
    context.last_response = context.api_client.get(
        f"/api/v1/user-notes/tags?subject_id={subject_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["tags_response"] = context.last_response.json()


@when('bob GET /api/v1/user-notes/tags')
def step_bob_list_tags(context):
    token = _token(context, "bob@example.com")
    context.last_response = context.api_client.get(
        "/api/v1/user-notes/tags",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["bob_tags_response"] = context.last_response.json()


# ── GET /api/v1/user-notes?tag= ───────────────────────────────────────────────

@when('alice GET /api/v1/user-notes?tag={tag}')
def step_alice_list_notes_by_tag(context, tag):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.get(
        f"/api/v1/user-notes?tag={tag}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["filtered_notes_response"] = context.last_response.json()
