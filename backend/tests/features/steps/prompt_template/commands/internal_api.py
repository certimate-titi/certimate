"""Internal API step definitions for prompt templates."""

from behave import when


@when('Internal API 請求模板 "{name}"')
def step_impl(context, name):
    """Call the internal prompt template API (no auth required)."""
    context.last_response = context.api_client.get(
        f"/api/v1/internal/prompt-templates/{name}"
    )
