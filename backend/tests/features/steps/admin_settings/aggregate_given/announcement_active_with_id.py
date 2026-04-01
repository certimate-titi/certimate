"""Given 系統中有一則 active 狀態的公告，ID 為 ... — Aggregate Given"""

from behave import given

from app.models.system_announcement import SystemAnnouncement


@given('系統中有一則 active 狀態的公告，ID 為 "{ann_key}"，標題為 "{title}"')
def step_impl(context, ann_key, title):
    db = context.db_session

    announcement = SystemAnnouncement(
        title=title,
        content=f"{title} 內容",
        type="info",
        display_mode="banner",
        status="active",
    )
    db.add(announcement)
    db.flush()

    context.ids[ann_key] = str(announcement.id)
    db.commit()
