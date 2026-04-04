"""Then 系統應套用預設 Bloom 配比 — ReadModel Then"""

from behave import then


@then('系統應套用預設 Bloom 配比（remember:20/understand:25/apply:25/analyze:15/evaluate:10/create:5）')
def step_impl(context):
    response = context.last_response
    data = response.json()

    bloom_source = data.get("bloom_source")
    assert bloom_source == "default", (
        f"bloom_source 應為 'default'，但得到 '{bloom_source}'"
    )
