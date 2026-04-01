"""Given 系統中有一則 active 狀態的公告，標題為 ...，顯示方式為 ... — Aggregate Given"""

from behave import given

from app.models.system_announcement import SystemAnnouncement


@given('系統中有一則 active 狀態的公告，標題為 "{title}"，顯示方式為 "{display_mode}"')
def step_impl(context, title, display_mode):
    db = context.db_session

    announcement = SystemAnnouncement(
        title=title,
        content=f"{title} 內容",
        type="info",
        display_mode=display_mode,
        status="active",
    )
    db.add(announcement)
    db.flush()

    # Store by title for later lookup
    context.ids[f"ann_title_{title}"] = str(announcement.id)
    db.commit()
