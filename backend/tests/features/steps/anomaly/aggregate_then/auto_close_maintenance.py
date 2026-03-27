"""Then 系統應自動關閉維修模式 — Aggregate Then"""

from behave import then

from app.models.maintenance_schedule import MaintenanceSchedule


@then('系統應自動關閉維修模式')
def step_impl(context):
    db = context.db_session
    db.expire_all()

    # Verify the active schedule is now completed
    schedule = db.query(MaintenanceSchedule).filter_by(status="active").first()
    assert schedule is None, "不應有任何 active 的維修排程"

    completed = db.query(MaintenanceSchedule).filter_by(status="completed").first()
    assert completed is not None, "應存在一個已完成的維修排程"


@then('用戶應能正常存取所有功能')
def step_user_can_access(context):
    # Verify no active full-site maintenance
    db = context.db_session
    db.expire_all()

    active = db.query(MaintenanceSchedule).filter_by(
        is_full_site=True, status="active"
    ).first()
    assert active is None, "不應有任何啟用的全站維修模式"
