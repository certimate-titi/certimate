"""Then 資源列表數量應為 — ReadModel Then"""

from behave import then


@then('資源列表數量應為 {count:d}')
def step_impl(context, count):
    response = context.last_response
    data = response.json()

    resources = data.get("resources", [])
    assert len(resources) == count, \
        f"預期資源數量 {count}，實際 {len(resources)}"
