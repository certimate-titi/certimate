"""Then 回應應包含基本資訊 — ReadModel Then"""

from behave import then


@then('回應應包含基本資訊：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    for row in context.table:
        field = row["欄位"]
        expected = row["值"]
        actual = str(data.get(field, ""))
        assert expected in actual, \
            f"欄位 '{field}' 預期包含 '{expected}'，實際 '{actual}'"
