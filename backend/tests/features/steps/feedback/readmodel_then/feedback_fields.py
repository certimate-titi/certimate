"""Then 每筆紀錄應包含：— Readmodel Then"""

from behave import then


@then('每筆紀錄應包含：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    items = data if isinstance(data, list) else data.get("items", data.get("feedbacks", []))
    assert len(items) > 0, "回應中沒有反饋紀錄"

    expected_fields = [row["欄位"] for row in context.table]

    for i, item in enumerate(items):
        for field in expected_fields:
            assert field in item, \
                f"第 {i + 1} 筆紀錄缺少欄位 '{field}'，實際欄位: {list(item.keys())}"
