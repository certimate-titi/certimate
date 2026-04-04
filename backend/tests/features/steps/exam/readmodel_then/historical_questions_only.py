"""Then 測驗應包含 N 題考古題 — ReadModel Then"""

from behave import then


@then('測驗應包含 {count:d} 題考古題')
def step_impl(context, count):
    response = context.last_response
    data = response.json()

    actual = data.get("total_questions")
    assert actual == count, (
        f"測驗應包含 {count} 題考古題，但得到 {actual}"
    )
