"""Then 系統應暫存使用者的學習偏好設定 — ReadModel Then"""

from behave import then


@then('系統應暫存使用者的學習偏好設定')
def step_impl(context):
    response = context.last_response
    assert response.status_code in [200, 201], \
        f"預期成功（2XX），實際 {response.status_code}: {response.text}"
