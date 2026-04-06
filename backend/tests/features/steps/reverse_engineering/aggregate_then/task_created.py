"""Then 系統應建立一筆逆向工程任務 — Aggregate Then"""

from behave import then

from app.models.reverse_engineering_task import ReverseEngineeringTask


@then('系統應建立一筆逆向工程任務，狀態為 "{status}"')
def step_impl(context, status):
    db = context.db_session

    task = db.query(ReverseEngineeringTask).filter_by(status=status).first()
    assert task is not None, \
        f"預期找到狀態為 '{status}' 的逆向工程任務，但未找到"
    assert task.status == status, \
        f"預期任務狀態為 '{status}'，實際為 '{task.status}'"
