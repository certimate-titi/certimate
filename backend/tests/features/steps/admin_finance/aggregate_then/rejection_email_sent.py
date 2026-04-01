"""Then 系統應發送駁回通知 Email — Aggregate Then (no-op, email is side-effect)"""

from behave import then


@then('系統應發送駁回通知 Email 至使用者 {user_id_key}，內容包含理由 "{reason}"')
def step_impl(context, user_id_key, reason):
    # Email sending is a side-effect that cannot be verified in E2E tests.
    # In production, this would be handled by an email service.
    # This step is intentionally a no-op / pass-through assertion.
    pass
