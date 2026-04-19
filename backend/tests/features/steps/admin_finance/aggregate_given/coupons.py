"""Given 系統中有以下優惠碼 — Aggregate Given"""

from behave import given

from app.models.coupon import Coupon


@given('系統中有以下優惠碼：')
def step_impl(context):
    db = context.db_session
    for row in context.table:
        coupon = Coupon(
            code=row["代碼"],
            discount_type=row["折扣類型"],
            discount_value=float(row["折扣值"]),
            status="active",
        )
        db.add(coupon)
    db.commit()
