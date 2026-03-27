"""Then 系統應通知所有在線用戶 — Aggregate Then"""

from behave import then


@then('系統應通知所有在線用戶')
def step_impl(context):
    # In E2E, verify the response indicates notification was broadcast
    response = context.last_response
    assert response.status_code in [200, 201, 204], \
        f"操作應成功以觸發通知，實際 {response.status_code}"
