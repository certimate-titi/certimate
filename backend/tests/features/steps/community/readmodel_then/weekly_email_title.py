"""Then step: Email 標題應包含「學習週報」"""

from behave import then


@then('Email 標題應包含「學習週報」')
def step_impl(context):
    email = context.memo.get("last_weekly_email", {})
    subject = email.get("subject", "")
    assert "學習週報" in subject, \
        f"Email subject does not contain '學習週報': {subject}"
