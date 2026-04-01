"""When 使用者刪除公告 — Command"""

from behave import when


@when('使用者 "{email}" 刪除公告 "{ann_key}"')
def step_impl(context, email, ann_key):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    announcement_id = context.ids[ann_key]

    response = context.api_client.delete(
        f"/api/v1/admin/system-settings/announcements/{announcement_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
