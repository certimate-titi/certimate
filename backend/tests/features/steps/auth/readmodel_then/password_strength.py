from behave import then


@then('密碼強度指示條應顯示 "{level}"')
def step_impl(context, level):
    response = context.last_response
    data = response.json()
    actual_level = data.get("strength") or data.get("level")
    assert actual_level is not None, \
        f"回應中找不到密碼強度欄位: {data}"
    assert actual_level == level, \
        f"密碼強度應為 '{level}'，實際為 '{actual_level}'"
