"""Then 優惠碼狀態驗證 — Aggregate Then"""

from behave import then

from app.models.coupon import Coupon


@then('優惠碼 "{code}" 的狀態應為 "{expected_status}"')
def step_impl(context, code, expected_status):
    db = context.db_session
    db.expire_all()

    coupon = db.query(Coupon).filter_by(code=code).first()
    assert coupon is not None, f"找不到優惠碼 {code}"
    actual = coupon.status.value if hasattr(coupon.status, "value") else str(coupon.status)
    assert actual == expected_status, \
        f"優惠碼 {code} 狀態應為 '{expected_status}'，實際 '{actual}'"


@then('優惠碼 "{code}" 的已使用次數應為 {expected_count:d}')
def step_impl_used_count(context, code, expected_count):
    db = context.db_session
    db.expire_all()

    coupon = db.query(Coupon).filter_by(code=code).first()
    assert coupon is not None, f"找不到優惠碼 {code}"
    assert coupon.used_count == expected_count, \
        f"優惠碼 {code} 已使用次數應為 {expected_count}，實際 {coupon.used_count}"
