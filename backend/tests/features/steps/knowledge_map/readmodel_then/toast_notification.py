from behave import then


@then('儀表板應顯示 Toast 通知「{message}」')
def step_impl(context, message):
    response = context.last_response
    assert response is not None, "沒有 HTTP 回應"
    assert response.status_code in [200, 201], \
        f"API 回應失敗: {response.status_code} - {response.text}"

    data = response.json()
    notification = data.get("notification") or data.get("message")
    assert notification is not None, f"回應中找不到通知訊息: {data}"
    assert message in str(notification), \
        f"通知訊息應包含「{message}」，實際為「{notification}」"
