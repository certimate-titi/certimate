"""Then 異常狀態驗證 — Aggregate Then"""

from behave import then

from app.models.anomaly_record import AnomalyRecord


@then('異常 "{error_id}" 的狀態應為 "{expected_status}"')
def step_impl(context, error_id, expected_status):
    db = context.db_session
    db.expire_all()
    record = db.query(AnomalyRecord).filter_by(error_id=error_id).first()
    assert record is not None, f"找不到異常紀錄 '{error_id}'"
    assert record.status == expected_status, \
        f"異常 '{error_id}' 狀態應為 '{expected_status}'，實際為 '{record.status}'"
