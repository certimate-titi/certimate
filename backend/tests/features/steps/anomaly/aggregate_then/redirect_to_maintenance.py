"""Then 所有非管理後台的請求應導向維修頁面 — Aggregate Then"""

from behave import then

from app.models.maintenance_schedule import MaintenanceSchedule


@then('所有非管理後台的請求應導向維修頁面')
def step_impl(context):
    db = context.db_session
    db.expire_all()

    # Verify there is an active full-site maintenance schedule
    schedule = db.query(MaintenanceSchedule).filter_by(
        is_full_site=True, status="active"
    ).first()
    assert schedule is not None, "應存在一個啟用的全站維修排程"
