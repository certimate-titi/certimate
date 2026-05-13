"""When — Feature 51 筆記重置 API 呼叫。"""

from behave import when


def _token(context, email: str) -> str:
    return context.jwt_helper.generate_token(context.ids[email])


# ── DELETE /api/v1/user-notes/all ────────────────────────────────────────────

@when("alice DELETE /api/v1/user-notes/all")
def step_alice_delete_all_user_notes(context):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.delete(
        "/api/v1/user-notes/all",
        headers={"Authorization": f"Bearer {token}"},
    )


@when("未認證 DELETE /api/v1/user-notes/all")
def step_unauth_delete_all_user_notes(context):
    context.last_response = context.api_client.delete("/api/v1/user-notes/all")


# ── DELETE /api/v1/chat-annotations/all ──────────────────────────────────────

@when("alice DELETE /api/v1/chat-annotations/all")
def step_alice_delete_all_chat_annotations(context):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.delete(
        "/api/v1/chat-annotations/all",
        headers={"Authorization": f"Bearer {token}"},
    )


@when("未認證 DELETE /api/v1/chat-annotations/all")
def step_unauth_delete_all_chat_annotations(context):
    context.last_response = context.api_client.delete("/api/v1/chat-annotations/all")


# ── POST /api/v1/knowledge-map/scaffolds/reset-responses ─────────────────────

@when("alice POST /api/v1/knowledge-map/scaffolds/reset-responses")
def step_alice_reset_scaffold_responses(context):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.post(
        "/api/v1/knowledge-map/scaffolds/reset-responses",
        headers={"Authorization": f"Bearer {token}"},
    )


@when("未認證 POST /api/v1/knowledge-map/scaffolds/reset-responses")
def step_unauth_reset_scaffold_responses(context):
    context.last_response = context.api_client.post(
        "/api/v1/knowledge-map/scaffolds/reset-responses"
    )
