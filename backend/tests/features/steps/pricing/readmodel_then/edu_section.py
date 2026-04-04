"""Then 回應應包含教育方案說明區塊 — ReadModel Then"""

from behave import then


@then('回應應包含教育方案說明區塊：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    edu = data.get("edu_section")
    assert edu is not None, "回應缺少 edu_section"

    for row in context.table:
        field = row["欄位"]
        assert field in edu, f"教育方案說明缺少欄位 '{field}'"
