"""Then 公告 is_active 應為 — Aggregate Then (feature 24)"""

from behave import then

from app.models.system_announcement import SystemAnnouncement


@then('公告 "{title}" 的 is_active 應為 false')
def step_announcement_is_active_false(context, title):
    """驗證指定標題的公告已被停用（status == inactive）。"""
    db = context.db_session
    db.expire_all()

    announcement_id = context.ids.get(title)
    if announcement_id:
        announcement = db.query(SystemAnnouncement).filter(
            SystemAnnouncement.id == announcement_id
        ).first()
    else:
        announcement = db.query(SystemAnnouncement).filter(
            SystemAnnouncement.title == title
        ).first()

    assert announcement is not None, f"找不到標題為 '{title}' 的公告"
    assert announcement.status == "inactive", \
        f"公告 '{title}' 應為停用（inactive），實際 '{announcement.status}'"
