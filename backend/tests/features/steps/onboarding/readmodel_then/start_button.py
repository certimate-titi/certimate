"""Then 畫面應顯示開始我的學習旅程按鈕 — ReadModel Then"""

from behave import then


@then('畫面應顯示「開始我的學習旅程」按鈕')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("show_start_button") is True, \
        f"預期 show_start_button=True，實際: {data.get('show_start_button')}"
