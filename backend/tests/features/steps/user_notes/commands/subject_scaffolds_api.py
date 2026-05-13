"""When — GET subject-level scaffolds API commands（Feature 50）。"""

import uuid

from behave import when


def _token(context, email: str) -> str:
    return context.jwt_helper.generate_token(context.ids[email])


@when("alice GET /api/v1/knowledge-map/subjects/<subject_id>/scaffolds?user_response_only=true")
def step_alice_get_subject_scaffolds(context):
    subject_id = context.memo["subject_id"]
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.get(
        f"/api/v1/knowledge-map/subjects/{subject_id}/scaffolds?user_response_only=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 200:
        context.memo["subject_scaffolds_response"] = context.last_response.json()


@when("bob GET /api/v1/knowledge-map/subjects/<subject_id>/scaffolds?user_response_only=true")
def step_bob_get_subject_scaffolds(context):
    subject_id = context.memo["subject_id"]
    token = _token(context, "bob@example.com")
    context.last_response = context.api_client.get(
        f"/api/v1/knowledge-map/subjects/{subject_id}/scaffolds?user_response_only=true",
        headers={"Authorization": f"Bearer {token}"},
    )


@when("alice GET /api/v1/knowledge-map/subjects/<nonexistent_subject_id>/scaffolds")
def step_alice_get_nonexistent_subject_scaffolds(context):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.get(
        f"/api/v1/knowledge-map/subjects/{uuid.uuid4()}/scaffolds",
        headers={"Authorization": f"Bearer {token}"},
    )
