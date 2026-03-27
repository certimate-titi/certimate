"""Then 已選科目列表應顯示 N 個科目及其設定 — ReadModel Then"""

from behave import then


@then('已選科目列表應顯示 {count:d} 個科目及其設定')
def step_impl(context, count):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    selected = data.get("selected_subjects", [])
    assert len(selected) == count, \
        f"預期 {count} 個已選科目，實際 {len(selected)}"
