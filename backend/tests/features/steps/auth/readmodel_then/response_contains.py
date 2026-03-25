from behave import then


@then('登入後的回應應包含 "{key}": "{value}"')
def step_impl(context, key, value):
    response = context.last_response
    data = response.json()
    user_data = data.get("user", data)

    actual_value = user_data.get(key)
    assert actual_value is not None, \
        f"回應中找不到欄位 '{key}': {user_data}"
    assert str(actual_value) == value, \
        f"欄位 '{key}' 應為 '{value}'，實際為 '{actual_value}'"
