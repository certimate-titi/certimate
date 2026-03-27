"""Then step: 系統不應發送喚回通知至 "{email}" """

from behave import then


@then('系統不應發送喚回通知至 "{email}"')
def step_impl(context, email):
    data = context.last_response.json()
    notifications = data.get("notifications", [])

    found = any(n.get("email") == email for n in notifications)
    assert not found, f"Unexpected notification sent to {email}: {notifications}"
