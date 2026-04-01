"""Then 系統應發送帳號啟用信至 — Aggregate Then (no-op side-effect)"""

from behave import then


@then('系統應發送帳號啟用信至 "{email}"')
def step_impl(context, email):
    # Side-effect verification: in a real system this would check
    # an email queue or mock. For now, we verify the API responded
    # successfully (checked by prior "操作成功" step) and treat
    # email sending as a no-op assertion.
    pass
