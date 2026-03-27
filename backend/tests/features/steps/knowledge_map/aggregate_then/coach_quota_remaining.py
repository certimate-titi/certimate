"""Then 使用者的高階教練剩餘額度驗證 — Aggregate Then"""

from behave import then


@then('使用者 "{email}" 的高階教練剩餘額度應為 {count:d}')
def step_impl(context, email, count):
    response = context.last_response
    data = response.json()

    remaining = data.get("remaining_quota", data.get("coach_quota_remaining"))
    assert remaining is not None, "回應中缺少剩餘額度欄位"
    assert int(remaining) == count, (
        f"使用者 '{email}' 的高階教練剩餘額度應為 {count}，但得到 {remaining}"
    )
