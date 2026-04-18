"""Then 資源詳情回應欄位驗證 — ReadModel Then"""

from behave import then


@then('回應欄位 "{field}" 應為 "{expected}"')
def step_impl_field_equals(context, field, expected):
    response = context.last_response
    assert response is not None, "context.last_response 為 None"
    try:
        data = response.json()
    except Exception as e:
        assert False, f"無法解析 JSON: {e}"
    actual = data.get(field)
    assert str(actual) == expected, \
        f"欄位 '{field}' 期望 '{expected}'，實際 '{actual}'"
