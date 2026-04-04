"""Then 系統應自動套用考古題 Bloom 配比作為出題依據 — ReadModel Then"""

from behave import then


@then('系統應自動套用考古題 Bloom 配比作為出題依據')
def step_impl(context):
    response = context.last_response
    data = response.json()

    bloom_source = data.get("bloom_source")
    assert bloom_source == "historical", (
        f"bloom_source 應為 'historical'，但得到 '{bloom_source}'"
    )
