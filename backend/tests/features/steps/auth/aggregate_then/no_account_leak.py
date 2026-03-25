from behave import then


@then('系統不應洩漏該帳號是否存在的資訊')
def step_impl(context):
    response = context.last_response
    data = response.json()
    # 回應訊息不應包含「帳號不存在」或「找不到」等洩漏資訊的字眼
    message = str(data.get("message", ""))
    leak_keywords = ["不存在", "找不到", "not found", "no account"]
    for keyword in leak_keywords:
        assert keyword not in message.lower(), \
            f"回應訊息洩漏帳號資訊，包含 '{keyword}': {message}"
