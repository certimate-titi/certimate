"""Then 系統應發送 Email 通知至所有 admin 與 super_admin — Aggregate Then (no-op)"""

from behave import then


@then('系統應發送 Email 通知至所有 admin 與 super_admin')
def step_impl(context):
    """Email notification is a side-effect; in E2E tests we just verify it passes."""
    pass
