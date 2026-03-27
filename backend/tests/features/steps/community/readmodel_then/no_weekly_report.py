"""Then step: 系統不應為使用者 "{email}" 生成週報"""

from behave import then


@then('系統不應為使用者 "{email}" 生成週報')
def step_impl(context, email):
    data = context.last_response.json()
    reports = data.get("reports", [])

    for r in reports:
        assert r.get("user_email") != email, \
            f"Unexpected report generated for {email}: {r}"
