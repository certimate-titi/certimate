"""Then 系統應開啟科目選擇介面 — ReadModel Then"""

from behave import then


@then('系統應開啟科目選擇介面')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    assert "subjects" in data or "categories" in data, \
        f"回應缺少科目選擇相關欄位: {data}"
