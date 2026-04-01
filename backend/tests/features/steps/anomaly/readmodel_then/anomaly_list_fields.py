"""Then 回應中每筆紀錄應包含 — Readmodel Then"""

from behave import then


@then('回應中每筆紀錄應包含：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    if isinstance(data, list):
        items = data
    else:
        items = data.get("items", data.get("data", data.get("logs", [])))

    expected_fields = [row["欄位"] for row in context.table]

    for item in items:
        for field in expected_fields:
            assert field in item, \
                f"紀錄缺少欄位 '{field}'，實際欄位: {list(item.keys())}"
