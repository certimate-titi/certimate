"""Then 回應應包含升級提示 — ReadModel Then"""

from behave import then


@then('回應應包含升級提示：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    # HTTPException wraps detail as {"detail": {"message": ..., "upgrade": {...}}}
    detail = data.get("detail", data)
    if isinstance(detail, str):
        detail = data
    upgrade_info = detail.get("upgrade", detail)

    for row in context.table:
        field = row['欄位']
        expected = row['值']
        actual = str(upgrade_info.get(field, ""))
        assert actual == expected, (
            f"升級提示 '{field}' 應為 '{expected}'，但得到 '{actual}'"
        )
