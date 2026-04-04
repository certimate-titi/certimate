"""Then 回應中學員列表應為空 — ReadModel Then"""

from behave import then


@then('回應中學員列表應為空')
def step_impl(context):
    response = context.last_response
    data = response.json()
    students = data.get("students", [])
    assert len(students) == 0, \
        f"預期學員列表為空，實際有 {len(students)} 位學員"
