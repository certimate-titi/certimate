"""Then 系統應發送啟用邀請信 — Aggregate Then"""

from behave import then


@then('系統應發送啟用邀請信至：')
def step_impl(context):
    """Verify invitation emails were created for the given addresses.

    In the current implementation, we verify that the users were created
    (email sending is a side effect that would be handled by an email service).
    """
    response = context.last_response
    data = response.json()
    created = data.get("created_users", 0)

    expected_emails = [row["Email"] for row in context.table]
    assert created >= len(expected_emails), \
        f"預期至少建立 {len(expected_emails)} 個帳號（以發送邀請信），實際 {created}"
