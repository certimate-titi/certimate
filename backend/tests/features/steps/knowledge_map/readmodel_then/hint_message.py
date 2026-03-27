from behave import then


@then('提示訊息應為「{message}」')
def step_impl(context, message):
    response = context.last_response
    assert response is not None, "沒有 HTTP 回應"

    data = response.json()
    hint = data.get("hint") or data.get("message")
    assert hint is not None, f"回應中找不到提示訊息: {data}"
    assert hint == message, \
        f"提示訊息應為「{message}」，實際為「{hint}」"
