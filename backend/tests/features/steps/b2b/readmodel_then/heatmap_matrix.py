"""Then 回應應包含矩陣結構 — ReadModel Then"""

from behave import then


@then('回應應包含矩陣結構：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    for row in context.table:
        field = row["欄位"]
        actual = data.get(field)
        assert actual is not None, \
            f"回應中找不到欄位 '{field}'，回應: {list(data.keys())}"
