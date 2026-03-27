"""Then 系統應排定通知 — Aggregate Then"""

from behave import then

from app.models.maintenance_notification import MaintenanceNotification


@then('系統應排定在 {time1} 與 {time2} 發送通知')
def step_impl(context, time1, time2):
    db = context.db_session
    db.expire_all()

    notifications = db.query(MaintenanceNotification).all()
    assert len(notifications) >= 2, \
        f"應排定至少 2 個通知，實際 {len(notifications)}"

    scheduled_times = [n.scheduled_send_at.strftime("%Y-%m-%dT%H:%M:%S") for n in notifications]
    assert time1 in scheduled_times, \
        f"應排定 {time1} 的通知，實際排定: {scheduled_times}"
    assert time2 in scheduled_times, \
        f"應排定 {time2} 的通知，實際排定: {scheduled_times}"
