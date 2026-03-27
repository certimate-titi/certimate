"""Then 教練面板應顯示溯源資訊 — ReadModel Then"""

from behave import then


@then('教練面板應顯示溯源資訊：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    source_info = data.get("source_info", data)

    for row in context.table:
        field = row['欄位']
        expected = row['值']
        actual = str(source_info.get(field, ""))
        assert actual == expected, (
            f"溯源資訊 '{field}' 應為 '{expected}'，但得到 '{actual}'"
        )
