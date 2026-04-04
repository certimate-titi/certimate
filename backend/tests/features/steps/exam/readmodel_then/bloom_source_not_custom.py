"""Then 測驗任務的 bloom_source 應為 default（非 custom）— ReadModel Then"""

from behave import then


@then('測驗任務的 bloom_source 應為 "default"（非 custom）')
def step_impl(context):
    response = context.last_response
    data = response.json()

    actual = data.get("bloom_source")
    assert actual == "default", (
        f"bloom_source 應為 'default'（非 custom），但得到 '{actual}'"
    )
    assert actual != "custom", (
        f"bloom_source 不應為 'custom'"
    )
