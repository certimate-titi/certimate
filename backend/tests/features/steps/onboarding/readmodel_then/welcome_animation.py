"""Then 畫面應顯示歡迎動畫 — ReadModel Then"""

from behave import then


@then('畫面應顯示歡迎動畫')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("show_welcome_animation") is True, \
        f"預期回應包含 show_welcome_animation=True，實際: {data}"
