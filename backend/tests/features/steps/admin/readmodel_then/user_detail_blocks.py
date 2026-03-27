"""Then 回應應包含以下區塊 — Read Model Then"""

from behave import then


@then('回應應包含以下區塊：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    for row in context.table:
        block = row["區塊"]
        assert block in data, \
            f"回應中缺少區塊 '{block}'，實際欄位：{list(data.keys())}"
