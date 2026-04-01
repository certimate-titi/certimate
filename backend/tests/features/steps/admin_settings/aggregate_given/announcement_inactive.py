"""Given 系統中有一則 inactive 狀態的公告，標題為 ... — Aggregate Given"""

from behave import given

from app.models.system_announcement import SystemAnnouncement


@given('系統中有一則 inactive 狀態的公告，標題為 "{title}"')
def step_impl(context, title):
    db = context.db_session

    announcement = SystemAnnouncement(
        title=title,
        content=f"{title} 內容",
        type="info",
        display_mode="banner",
        status="inactive",
    )
    db.add(announcement)
    db.flush()

    context.ids[f"ann_title_{title}"] = str(announcement.id)
    db.commit()
