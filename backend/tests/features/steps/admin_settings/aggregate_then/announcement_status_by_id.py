"""Then 公告 ID 的狀態應為 — Aggregate Then"""

from behave import then

from app.models.system_announcement import SystemAnnouncement


@then('公告 "{ann_key}" 的狀態應為 "{expected_status}"')
def step_impl(context, ann_key, expected_status):
    db = context.db_session
    db.expire_all()

    announcement_id = context.ids[ann_key]
    announcement = db.query(SystemAnnouncement).filter(
        SystemAnnouncement.id == announcement_id
    ).first()

    assert announcement is not None, f"找不到公告 '{ann_key}' (ID: {announcement_id})"
    assert announcement.status == expected_status, \
        f"公告 '{ann_key}' 狀態應為 '{expected_status}'，實際 '{announcement.status}'"
