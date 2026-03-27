"""Then 回應中每筆紀錄應包含 — Readmodel Then"""

from behave import then


@then('回應中每筆紀錄應包含：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    items = data if isinstance(data, list) else data.get("items", data.get("data", []))
    assert len(items) > 0, f"回應中沒有紀錄，response: {data}"

    expected_fields = [row["欄位"] for row in context.table]

    for item in items:
        for field in expected_fields:
            assert field in item, \
                f"紀錄缺少欄位 '{field}'，實際欄位: {list(item.keys())}"
