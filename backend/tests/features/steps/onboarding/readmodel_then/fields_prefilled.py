"""Then 各欄位應預填使用者目前的設定值 — ReadModel Then"""

from behave import then


@then('各欄位應預填使用者目前的設定值')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    fields = data.get("fields", [])

    for field in fields:
        value = field.get("value")
        assert value is not None, \
            f"欄位 '{field.get('label')}' 沒有預填值"
