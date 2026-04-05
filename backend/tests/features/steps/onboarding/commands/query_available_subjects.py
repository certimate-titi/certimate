"""When 使用者查詢可選科目清單 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查詢可選科目清單')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/subjects/available",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
