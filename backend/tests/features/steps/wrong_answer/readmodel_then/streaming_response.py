"""Then 回應應以串流方式輸出 — ReadModel Then"""

from behave import then


@then('回應應以串流方式輸出')
def step_impl(context):
    response = context.last_response
    data = response.json()
    assert data.get("streaming") is True, \
        f"預期 streaming=True，實際 {data.get('streaming')}"
