"""Then 畫面應顯示以下可編輯欄位 — ReadModel Then"""

from behave import then


@then('畫面應顯示以下可編輯欄位：')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    fields = data.get("fields", [])

    for row in context.table:
        field_name = row["欄位"]
        found = any(f.get("label") == field_name for f in fields)
        assert found, \
            f"回應中找不到欄位 '{field_name}'，實際欄位: {[f.get('label') for f in fields]}"
