"""Then 測驗任務的 bloom_source 應為 — ReadModel Then"""

from behave import then


@then('測驗任務的 bloom_source 應為 "{source}"')
def step_impl(context, source):
    response = context.last_response
    data = response.json()

    actual = data.get("bloom_source")
    assert actual == source, (
        f"bloom_source 應為 '{source}'，但得到 '{actual}'"
    )
