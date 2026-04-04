"""Then step: 系統不應寄送 Email 至 "{email}" """

from behave import then


@then('系統不應寄送 Email 至 "{email}"')
def step_impl(context, email):
    data = context.last_response.json()
    emails_sent = data.get("emails_sent", [])
    found = any(e.get("to") == email for e in emails_sent)
    assert not found, \
        f"Unexpected email sent to {email}: {emails_sent}"
