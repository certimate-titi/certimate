"""Then step: 系統應寄送週報 Email 至 "{email}" """

from behave import then


@then('系統應寄送週報 Email 至 "{email}"')
def step_impl(context, email):
    data = context.last_response.json()
    emails_sent = data.get("emails_sent", [])
    found = None
    for e in emails_sent:
        if e.get("to") == email:
            found = e
            break
    assert found is not None, \
        f"No weekly email sent to {email}. Emails sent: {emails_sent}"
    context.memo["last_weekly_email"] = found
