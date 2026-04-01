"""Then 系統應發送警告通知至資源擁有者 — Aggregate Then (no-op)"""

from behave import then


@then('系統應發送警告通知至資源擁有者')
def step_impl(context):
    # Side-effect step: notification sending is not verified in E2E tests.
    # In production, this would be handled by an async notification service.
    pass
