"""Then 回應應包含生成的題目總數 — ReadModel Then"""

from behave import then


@then('回應應包含生成的題目總數 {count:d}')
def step_impl(context, count):
    response = context.last_response
    data = response.json()

    actual = data.get("total_questions")
    assert actual == count, (
        f"題目總數應為 {count}，但得到 {actual}"
    )
