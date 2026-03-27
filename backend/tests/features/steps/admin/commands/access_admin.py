"""When 使用者存取管理後台 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 存取管理後台')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
