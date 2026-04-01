"""Given 使用者在帳號設定頁的「個人資料」分頁 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 在帳號設定頁的「個人資料」分頁')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_email"] = email

    # Fetch profile page to set context.last_response
    response = context.api_client.get(
        "/api/v1/dashboard/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
