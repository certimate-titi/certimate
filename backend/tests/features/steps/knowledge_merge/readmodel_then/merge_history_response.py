"""Then 合併歷史紀錄驗證 — ReadModel Then"""

from behave import then


@then('回應應包含 {count:d} 筆合併紀錄')
def step_merge_history_count(context, count):
    response = context.last_response
    data = response.json()

    records = data.get("history", data.get("records", data.get("items", [])))
    actual_count = len(records)
    assert actual_count == count, \
        f"預期 {count} 筆合併紀錄，實際有 {actual_count} 筆，data: {data}"
