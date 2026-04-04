"""Then 測驗任務的 bloom_distribution 應符合自訂比例 — ReadModel Then"""

from behave import then


@then('測驗任務的 bloom_distribution 應符合自訂比例')
def step_impl(context):
    response = context.last_response
    data = response.json()

    actual_dist = data.get("bloom_distribution", {})
    expected_dist = context.memo.get("submitted_bloom_distribution", {})

    for category, pct in expected_dist.items():
        actual_pct = actual_dist.get(category)
        assert actual_pct == pct, (
            f"Bloom '{category}' 應為 {pct}%，但得到 {actual_pct}%"
        )
