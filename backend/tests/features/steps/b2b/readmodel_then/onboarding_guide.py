"""Then 回應應包含初始化引導資訊 — ReadModel Then"""

from behave import then


@then('回應應包含初始化引導資訊：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    for row in context.table:
        field = row["欄位"]
        expected = row["說明"]

        actual = data.get(field)
        assert actual is not None, \
            f"回應中找不到欄位 '{field}'，回應: {list(data.keys())}"

        # Handle boolean comparison
        if expected.lower() in ("true", "false"):
            expected_bool = expected.lower() == "true"
            assert actual == expected_bool, \
                f"欄位 '{field}': 預期 {expected}，實際 {actual}"
        else:
            assert str(expected) in str(actual), \
                f"欄位 '{field}': 預期包含 '{expected}'，實際 '{actual}'"
