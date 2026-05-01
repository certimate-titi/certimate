"""Given 系統中有以下公告 — Aggregate Given (feature 24)"""

from behave import given

from app.models.system_announcement import SystemAnnouncement


@given('系統中有以下公告：')
def step_seed_announcements_table(context):
    """批次建立公告，支援 table 格式：公告 ID / 標題 / 類型 / 啟用。"""
    db = context.db_session

    for row in context.table:
        ann_key = row.get("公告 ID", "")
        title = row.get("標題", "")
        ann_type = row.get("類型", "info")
        is_active_str = row.get("啟用", "true").strip().lower()
        status = "active" if is_active_str == "true" else "inactive"

        announcement = SystemAnnouncement(
            title=title,
            content=f"{title} 內容",
            type=ann_type,
            display_mode="banner",
            status=status,
        )
        db.add(announcement)
        db.flush()

        # Store by both ann_key and title
        context.ids[ann_key] = str(announcement.id)
        context.ids[title] = str(announcement.id)

    db.commit()


@given('系統中有啟用的公告 "{title}"')
def step_seed_active_announcement_by_title(context, title):
    """建立一則啟用中的公告（依標題）。"""
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

    context.ids[title] = str(announcement.id)
    db.commit()
