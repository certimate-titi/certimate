"""Then 頁面應顯示營運儀表板 — Read Model Then"""

from behave import then


@then('頁面應顯示營運儀表板')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    assert "dau" in data or "conversion_rate" in data, \
        f"回應中缺少儀表板欄位：{data}"
