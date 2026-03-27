"""Then 回應應包含以下 KPI 欄位 — Read Model Then"""

from behave import then


@then('回應應包含以下 KPI 欄位：')
def step_impl(context):
    response = context.last_response
    data = response.json()
    for row in context.table:
        field = row["欄位"]
        assert field in data, \
            f"KPI 欄位 '{field}' 不存在於回應中，實際欄位：{list(data.keys())}"
