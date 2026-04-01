"""Then 系統中不應存在公告 — Aggregate Then"""

from behave import then

from app.models.system_announcement import SystemAnnouncement


@then('系統中不應存在公告 "{ann_key}"')
def step_impl(context, ann_key):
    db = context.db_session
    db.expire_all()

    announcement_id = context.ids[ann_key]
    announcement = db.query(SystemAnnouncement).filter(
        SystemAnnouncement.id == announcement_id
    ).first()

    assert announcement is None, \
        f"公告 '{ann_key}' (ID: {announcement_id}) 不應存在，但仍在資料庫中"
