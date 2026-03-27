"""Then 每個科目旁應顯示可移除的按鈕 — ReadModel Then"""

from behave import then


@then('每個科目旁應顯示可移除的按鈕')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    selected = data.get("selected_subjects", [])
    for s in selected:
        assert s.get("removable") is True, \
            f"科目 '{s.get('name')}' 應為可移除，實際: {s}"
