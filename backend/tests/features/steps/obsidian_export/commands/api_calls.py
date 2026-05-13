"""When step API calls — Feature 53 Obsidian Export BDD."""

from behave import when


def _token(context, email: str) -> str:
    return context.jwt_helper.generate_token(context.ids[email])


@when("alice GET /api/v1/user-notes/export/obsidian")
def step_alice_export_obsidian(context):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.get(
        "/api/v1/user-notes/export/obsidian",
        headers={"Authorization": f"Bearer {token}"},
    )


@when("alice GET /api/v1/user-notes/export/obsidian?force=true")
def step_alice_export_obsidian_force(context):
    token = _token(context, "alice@example.com")
    context.last_response = context.api_client.get(
        "/api/v1/user-notes/export/obsidian?force=true",
        headers={"Authorization": f"Bearer {token}"},
    )


@when("bob GET /api/v1/user-notes/export/obsidian")
def step_bob_export_obsidian(context):
    token = _token(context, "bob@example.com")
    context.last_response = context.api_client.get(
        "/api/v1/user-notes/export/obsidian",
        headers={"Authorization": f"Bearer {token}"},
    )
