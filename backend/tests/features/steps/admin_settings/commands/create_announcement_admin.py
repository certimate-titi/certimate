"""When 管理員建立系統公告 — Command (feature 24)"""

from behave import when


@when('管理員 "{email}" 建立系統公告：')
def step_admin_create_announcement_table(context, email):
    """管理員透過 table 建立系統公告。"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    payload = {}
    for row in context.table:
        val = row["值"]
        # Convert boolean strings
        if val.lower() == "true":
            val = True
        elif val.lower() == "false":
            val = False
        payload[row["欄位"]] = val

    response = context.api_client.post(
        "/api/v1/admin/system-settings/announcements",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response

    # Store created announcement title → id for later lookup
    if response.status_code in (200, 201):
        data = response.json()
        ann = data.get("announcement", {})
        title = ann.get("title") or payload.get("title")
        ann_id = ann.get("id")
        if title and ann_id:
            context.ids[title] = ann_id
