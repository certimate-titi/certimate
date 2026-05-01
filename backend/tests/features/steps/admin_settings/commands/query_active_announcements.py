"""When 使用者查詢啟用中的公告 — Command (feature 24)"""

from behave import when


@when('使用者 "{email}" 查詢啟用中的公告')
def step_query_active_announcements(context, email):
    """使用者查詢啟用中的公告列表。"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/announcements",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
