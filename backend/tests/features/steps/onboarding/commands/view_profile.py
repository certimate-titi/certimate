"""When 使用者進入帳號設定頁的「個人資料」分頁 — Command (GET)"""

from behave import when


@when('使用者進入帳號設定頁的「個人資料」分頁')
def step_impl(context):
    email = context.memo.get("current_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_id = context.ids.get(email)
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_email"] = email

    response = context.api_client.get(
        "/api/v1/dashboard/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
