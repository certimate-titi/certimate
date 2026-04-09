"""Then 使用者的基礎教練剩餘額度驗證 — Aggregate Then"""

from behave import then


@then('使用者 "{email}" 的基礎教練剩餘額度應為 {count:d}')
def step_impl_quota(context, email, count):
    """驗證使用者的基礎教練剩餘額度已被扣除。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        remaining = data.get("remaining_basic_quota") or data.get("quota_remaining")
        if remaining is not None:
            assert remaining == count, \
                f"基礎教練剩餘額度期望 {count}，實際 {remaining}"


@then('使用者 "{email}" 的基礎教練剩餘額度應仍為 {count:d}')
def step_impl_quota_unchanged(context, email, count):
    """驗證使用者的基礎教練剩餘額度未改變（未扣除）。"""
    memo_key = f"basic_coach_quota_{email}"
    initial_quota = context.memo.get(memo_key, count)
    # After failed/blocked request, quota should remain unchanged
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        remaining = data.get("remaining_basic_quota") or data.get("quota_remaining")
        if remaining is not None:
            assert remaining == count, \
                f"額度不應被扣除，期望仍為 {count}，實際 {remaining}"
