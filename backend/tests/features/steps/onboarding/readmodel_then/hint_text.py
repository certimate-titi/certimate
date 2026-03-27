"""Then 畫面應顯示提示文字 — ReadModel Then"""

from behave import then


@then('畫面應顯示提示文字「{text}」')
def step_impl(context, text):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    hint = data.get("hint_text", "")
    assert text in hint, \
        f"預期提示文字包含 '{text}'，實際: '{hint}'"
