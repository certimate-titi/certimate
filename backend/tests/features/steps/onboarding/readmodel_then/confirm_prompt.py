"""Then 系統應提示確認 — ReadModel Then"""

from behave import then


@then('系統應提示確認 "{message}"')
def step_impl(context, message):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    confirm_msg = data.get("confirm_message", "")
    assert message in confirm_msg, \
        f"預期確認訊息包含 '{message}'，實際: '{confirm_msg}'"
