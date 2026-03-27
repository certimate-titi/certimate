"""Then 回應應包含訂閱資訊 — ReadModel Then"""

from behave import then


@then('回應應包含訂閱資訊：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    for row in context.table:
        field = row["欄位"]
        expected = row["值"]
        actual = str(data.get(field, ""))

        if expected == "null":
            assert data.get(field) is None, \
                f"欄位 '{field}' 預期為 null，實際 '{actual}'"
        else:
            assert expected in actual, \
                f"欄位 '{field}' 預期包含 '{expected}'，實際 '{actual}'"
