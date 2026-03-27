"""Then 公告狀態應為 — Aggregate Then"""

from behave import then

from app.models.system_announcement import SystemAnnouncement


@then('公告狀態應為 "{expected_status}"')
def step_impl(context, expected_status):
    db = context.db_session
    db.expire_all()
    announcements = db.query(SystemAnnouncement).all()
    assert len(announcements) > 0, "找不到任何系統公告"
    latest = announcements[-1]
    assert latest.status == expected_status, \
        f"公告狀態應為 '{expected_status}'，實際 '{latest.status}'"
