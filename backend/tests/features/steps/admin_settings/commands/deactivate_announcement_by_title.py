"""When 管理員停用公告（依標題）— Command (feature 24)"""

from behave import when


@when('管理員 "{email}" 停用公告 "{title}"')
def step_admin_deactivate_announcement_by_title(context, email, title):
    """管理員停用指定標題的公告。"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    announcement_id = context.ids[title]

    response = context.api_client.put(
        f"/api/v1/admin/system-settings/announcements/{announcement_id}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
