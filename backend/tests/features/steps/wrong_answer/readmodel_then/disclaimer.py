"""Then 介面應顯示免責聲明 — ReadModel Then"""

from behave import then


@then('介面應顯示免責聲明：「{message}」')
def step_impl(context, message):
    response = context.last_response
    data = response.json()
    disclaimer = data.get("disclaimer", "")
    assert message in disclaimer, \
        f"免責聲明應包含「{message}」，實際：{disclaimer}"
