"""Then 系統中應存在公告（依標題）— Aggregate Then (feature 24)"""

from behave import then

from app.models.system_announcement import SystemAnnouncement


@then('系統中應存在公告 "{title}"')
def step_announcement_exists_by_title(context, title):
    """驗證 DB 中存在指定標題的公告。"""
    db = context.db_session
    db.expire_all()

    announcement = db.query(SystemAnnouncement).filter(
        SystemAnnouncement.title == title
    ).first()

    assert announcement is not None, f"系統中應存在標題為 '{title}' 的公告，但未找到"
