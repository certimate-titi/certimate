"""Then 儀表板組件相關 — Readmodel Then"""

from behave import then


@then('回應應包含以下組件：')
def step_impl(context):
    data = context.last_response.json()
    for row in context.table:
        component = row["組件"]
        assert component in data, \
            f"回應中缺少組件 '{component}'，實際鍵值：{list(data.keys())}"
