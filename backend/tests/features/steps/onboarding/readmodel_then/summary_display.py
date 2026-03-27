"""Then 畫面應顯示完整的設定摘要 — ReadModel Then"""

from behave import then


@then('畫面應顯示完整的設定摘要')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    assert "subjects" in data, f"回應缺少 subjects 欄位: {data}"
    assert "display_name" in data or "daily_study_minutes" in data, \
        f"回應缺少摘要欄位: {data}"
