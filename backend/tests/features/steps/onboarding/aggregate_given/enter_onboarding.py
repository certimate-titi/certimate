"""Given 使用者進入首次登入引導頁 — Aggregate Given (Query)"""

from behave import given


@given('使用者 "{email}" 進入首次登入引導頁')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_email"] = email

    response = context.api_client.get(
        "/api/v1/onboarding/step/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
