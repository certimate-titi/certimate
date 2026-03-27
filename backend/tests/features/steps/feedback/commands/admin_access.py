"""When 使用者 "..." 嘗試存取管理員意見反饋清單 API — Command (GET)"""

from behave import when


@when('使用者 "{email}" 嘗試存取管理員意見反饋清單 API')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/feedback/admin/list",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
