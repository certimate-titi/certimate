"""Then 畫面應顯示「已儲存」提示 — ReadModel Then"""

from behave import then


@then('畫面應顯示「已儲存」提示')
def step_impl(context):
    response = context.last_response
    assert response.status_code in [200, 201], \
        f"預期成功（2XX），實際 {response.status_code}: {response.text}"
    data = response.json()
    message = data.get("message", "")
    assert "已儲存" in message or "saved" in message.lower(), \
        f"預期顯示「已儲存」提示，實際訊息: '{message}'"
