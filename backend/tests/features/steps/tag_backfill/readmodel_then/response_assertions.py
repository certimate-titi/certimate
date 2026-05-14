"""Then — Feature 55 Tag Backfill response assertions."""

from behave import then


@then('回應 {status_code:d}')
def step_response_status(context, status_code):
    assert context.last_response.status_code == status_code, (
        f"Expected {status_code}, got {context.last_response.status_code}: "
        f"{context.last_response.text}"
    )


@then('result.user_notes_processed >= {min_val:d}')
def step_user_notes_processed_gte(context, min_val):
    body = context.last_response.json()
    actual = body.get("user_notes_processed", -1)
    assert actual >= min_val, (
        f"Expected user_notes_processed >= {min_val}, got {actual}. Body: {body}"
    )
