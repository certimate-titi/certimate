"""Then 所有題目應來自考古題題庫 — ReadModel Then"""

from behave import then


@then('所有題目應來自考古題題庫（reliability 全部為 green）')
def step_impl(context):
    response = context.last_response
    data = response.json()

    questions = data.get("questions", [])
    for q in questions:
        reliability = q.get("reliability", q.get("source_type", ""))
        assert reliability in ("green", "historical"), (
            f"所有題目應來自考古題（green），但找到 '{reliability}'"
        )
