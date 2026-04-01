"""Then 回應應包含 N 筆每日 DAU 與 MAU 資料點 — Read Model Then"""

from behave import then


@then('回應應包含 {count:d} 筆每日 DAU 與 MAU 資料點')
def step_impl(context, count):
    response = context.last_response
    data = response.json()

    data_points = data.get("data_points", data.get("points", []))
    actual_count = len(data_points)
    assert actual_count == count, \
        f"預期 {count} 筆資料點，實際 {actual_count}"

    # Verify each data point has DAU and MAU fields
    for point in data_points:
        assert "dau" in point, f"資料點缺少 dau 欄位：{point}"
        assert "mau" in point, f"資料點缺少 mau 欄位：{point}"
