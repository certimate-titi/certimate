"""Then 回應應包含帳單記錄 — ReadModel Then"""

from behave import then


@then('回應應包含帳單記錄')
def step_impl(context):
    response = context.last_response
    data = response.json()

    invoices = data.get("invoices", [])
    assert len(invoices) > 0, "帳單記錄不應為空"
