"""Then 回應應包含升級引導 — ReadModel Then"""

from behave import then


@then('回應應包含升級引導：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    # upgrade_guidance may be in the response directly or in detail
    guidance = data.get("upgrade_guidance")
    if not guidance and "detail" in data:
        detail = data["detail"]
        if isinstance(detail, dict):
            guidance = detail.get("upgrade_guidance")

    assert guidance is not None, (
        f"回應應包含 upgrade_guidance，但得到 {data}"
    )

    for row in context.table:
        field = row["欄位"]
        expected = row["值"]

        actual = guidance.get(field)
        if expected == "true":
            assert actual is True, f"upgrade_guidance['{field}'] 應為 true，但得到 {actual}"
        elif expected.isdigit():
            assert str(actual) == expected, f"upgrade_guidance['{field}'] 應為 {expected}，但得到 {actual}"
        else:
            assert str(actual) == expected, f"upgrade_guidance['{field}'] 應為 '{expected}'，但得到 '{actual}'"
