"""Then 前端濫用監控 items 結構驗證 — ReadModel"""

from behave import then


@then('前端濫用監控清單應包含至少一筆冷卻紀錄')
def step_impl_items_not_empty(context):
    data = context.last_response.json()
    items = data.get("items", [])
    assert len(items) > 0, f"items 為空；實際: {data}"


@then('前端濫用監控第一筆的 status 應為 "{expected}"')
def step_impl_first_status(context, expected):
    items = context.last_response.json().get("items", [])
    assert items, "items 為空"
    actual = items[0].get("status")
    assert actual == expected, f"status 不符，期望 {expected}，實際 {actual}"


@then('前端濫用監控第一筆的 metric 欄位不應為空')
def step_impl_first_metric_not_empty(context):
    items = context.last_response.json().get("items", [])
    assert items, "items 為空"
    metric = items[0].get("metric")
    assert metric, f"metric 欄位為空；實際: {items[0]}"
