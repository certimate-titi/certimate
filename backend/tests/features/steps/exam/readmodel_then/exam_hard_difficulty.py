"""Then 系統應建立測驗任務，難易度分配中 Hard 佔比應為 100% (@ignore) — ReadModel Then"""

from behave import then


@then('系統應建立測驗任務，難易度分配中 Hard 佔比應為 100%')
def step_impl(context):
    response = context.last_response
    data = response.json()

    difficulty = data.get("difficulty_distribution", {})
    hard_pct = difficulty.get("hard", 0)
    assert hard_pct == 100, (
        f"Hard 佔比應為 100%，但得到 {hard_pct}%"
    )
