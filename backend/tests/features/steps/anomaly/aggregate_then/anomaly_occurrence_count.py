"""Then 異常的發生次數驗證 — Aggregate Then"""

from behave import then

from app.models.anomaly_record import AnomalyRecord


@then('異常 "{error_id}" 的發生次數應為 {count:d}')
def step_impl(context, error_id, count):
    db = context.db_session
    db.expire_all()
    record = db.query(AnomalyRecord).filter_by(error_id=error_id).first()
    assert record is not None, f"找不到異常紀錄 '{error_id}'"
    assert record.occurrence_count == count, \
        f"異常 '{error_id}' 發生次數應為 {count}，實際為 {record.occurrence_count}"
