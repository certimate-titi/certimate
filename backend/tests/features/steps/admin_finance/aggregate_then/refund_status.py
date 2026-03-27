"""Then 退款狀態驗證 — Aggregate Then"""

from behave import then

from app.models.refund import Refund


@then('退款 "{refund_id}" 的狀態應為 "{expected_status}"')
def step_impl(context, refund_id, expected_status):
    db = context.db_session
    db.expire_all()

    refund = db.query(Refund).filter_by(refund_id=refund_id).first()
    assert refund is not None, f"找不到退款 {refund_id}"
    actual = refund.status.value if hasattr(refund.status, "value") else str(refund.status)
    assert actual == expected_status, \
        f"退款 {refund_id} 狀態應為 '{expected_status}'，實際 '{actual}'"
