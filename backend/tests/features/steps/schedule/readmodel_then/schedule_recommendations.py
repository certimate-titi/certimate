"""Then 回應應包含排程建議 — ReadModel Then"""

from behave import then


@then('回應應包含排程建議')
def step_impl(context):
    response = context.last_response
    data = response.json()

    subjects = data.get("subjects", [])
    assert len(subjects) > 0, "排程建議不應為空"
