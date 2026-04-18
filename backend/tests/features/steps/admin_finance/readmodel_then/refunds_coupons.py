"""Then 退款清單 / 優惠碼清單 / 退款回應 / 優惠試算 — ReadModel"""

from behave import then


@then('退款清單應包含退款 "{refund_id}"')
def step_refund_contains(context, refund_id):
    items = context.last_response.json().get("refunds", [])
    codes = [it.get("refund_id") for it in items]
    assert refund_id in codes, f"清單未包含 {refund_id}；實際: {codes}"


@then('優惠碼清單應包含代碼 "{code}"')
def step_coupon_contains(context, code):
    items = context.last_response.json().get("coupons", [])
    codes = [it.get("code") for it in items]
    assert code in codes, f"清單未包含 {code}；實際: {codes}"


@then('回應應包含 refund_id 欄位')
def step_response_has_refund_id(context):
    data = context.last_response.json()
    assert data.get("refund_id"), f"refund_id 缺失；實際: {data}"


@then('回應的 status 應為 "{expected}"')
def step_response_status_field(context, expected):
    actual = context.last_response.json().get("status")
    assert actual == expected, f"status 不符，期望 {expected}，實際 {actual}"


@then('回應的 discount_amount 應為 {expected:f}')
def step_discount_amount(context, expected):
    actual = context.last_response.json().get("discount_amount")
    assert abs(float(actual) - expected) < 0.01, f"discount_amount 不符，期望 {expected}，實際 {actual}"


@then('回應的 final_amount 應為 {expected:f}')
def step_final_amount(context, expected):
    actual = context.last_response.json().get("final_amount")
    assert abs(float(actual) - expected) < 0.01, f"final_amount 不符，期望 {expected}，實際 {actual}"
