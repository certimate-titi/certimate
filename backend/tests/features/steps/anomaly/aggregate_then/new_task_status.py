"""Then 新任務的狀態驗證 — Aggregate Then"""

from behave import then


@then('新任務的狀態應為 "{expected_status}"')
def step_impl(context, expected_status):
    response = context.last_response
    data = response.json()

    actual_status = data.get("status")
    assert actual_status == expected_status, \
        f"新任務狀態應為 '{expected_status}'，實際為 '{actual_status}'"
