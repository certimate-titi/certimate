"""Then step: 系統應發送 Email 通知至 "{email}" """

from behave import then


@then('系統應發送 Email 通知至 "{email}"')
def step_impl(context, email):
    data = context.last_response.json()
    notifications = data.get("notifications", [])

    found = any(n.get("email") == email for n in notifications)
    assert found, f"No notification sent to {email}. Notifications: {notifications}"

    # Store for subsequent steps
    for n in notifications:
        if n.get("email") == email:
            context.memo["last_notification"] = n
            break
