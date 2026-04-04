"""Then 測驗中考古題佔比應不低於 60% — ReadModel Then"""

from behave import then


@then('測驗中考古題（reliability 為 green）佔比應不低於 60%（在題庫充足時）')
def step_impl(context):
    response = context.last_response
    data = response.json()

    historical_ratio = data.get("historical_ratio", 0)
    assert historical_ratio >= 60, (
        f"考古題佔比應不低於 60%，但得到 {historical_ratio}%"
    )
