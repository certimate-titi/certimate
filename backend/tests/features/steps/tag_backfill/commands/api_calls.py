"""When — Feature 55 Tag Backfill command steps."""

from behave import when


@when('POST /api/v1/admin/backfill-tags 由 {email} 呼叫')
def step_post_backfill_tags(context, email):
    """呼叫 POST /api/v1/admin/backfill-tags。"""
    email = email.strip()
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/admin/backfill-tags",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
