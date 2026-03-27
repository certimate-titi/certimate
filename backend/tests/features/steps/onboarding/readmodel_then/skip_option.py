"""Then 使用者可填寫資訊或直接跳過進入下一步 — ReadModel Then"""

from behave import then


@then('使用者可填寫資訊或直接跳過進入下一步')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("can_skip") is True, \
        f"預期 can_skip=True，實際: {data.get('can_skip')}"
