"""When 使用者建立系統公告 — Command"""

from behave import when


def _do_create_announcement(context, email, title, content, ann_type):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # Strip surrounding quotes if present
    title_val = title.strip('"') if title else ""
    content_val = content.strip('"') if content else ""

    payload = {
        "title": title_val,
        "content": content_val,
        "type": ann_type,
    }

    response = context.api_client.post(
        "/api/v1/admin/system-settings/announcements",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


# Scenario Outline generates these exact step texts when cells are empty (no quotes):
@when(u'使用者 "super@certimate.com" 建立系統公告，標題為 ，內容為 2026/04/01 維護，類型為 "info"')
def step_outline_no_title(context):
    _do_create_announcement(context, "super@certimate.com", "", "2026/04/01 維護", "info")


@when(u'使用者 "super@certimate.com" 建立系統公告，標題為 系統維護通知，內容為 ，類型為 "info"')
def step_outline_no_content(context):
    _do_create_announcement(context, "super@certimate.com", "系統維護通知", "", "info")


@when('使用者 "{email}" 建立系統公告：')
def step_impl_table(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    payload = {}
    for row in context.table:
        payload[row["欄位"]] = row["值"]

    response = context.api_client.post(
        "/api/v1/admin/system-settings/announcements",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
