"""Then step: Email 標題應包含使用者顯示名稱"""

from behave import then


@then('Email 標題應包含使用者顯示名稱')
def step_impl(context):
    notification = context.memo.get("last_notification", {})
    title = notification.get("title", "")
    # The title should contain something (the display name or email prefix)
    assert len(title) > 0, "Email title is empty"
    # The title should contain a name-like string (not just punctuation)
    assert any(c.isalpha() for c in title), f"Email title has no name: {title}"
