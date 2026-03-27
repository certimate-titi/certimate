"""Then 維修任務狀態驗證 — Aggregate Then"""

from behave import then

from app.models.maintenance_task import MaintenanceTask


@then('任務 "{task_id}" 的狀態應為 "{expected_status}"')
def step_impl(context, task_id, expected_status):
    db = context.db_session
    db.expire_all()
    task = db.query(MaintenanceTask).filter_by(task_id=task_id).first()
    assert task is not None, f"找不到維修任務 '{task_id}'"
    assert task.status == expected_status, \
        f"任務 '{task_id}' 狀態應為 '{expected_status}'，實際為 '{task.status}'"
