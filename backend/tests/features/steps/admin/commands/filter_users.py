"""When 使用者篩選用戶（依方案） — Command (GET)"""

from behave import when


@when('使用者 "{email}" 篩選用戶，方案為 "{plan}"')
def step_impl(context, email, plan):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/admin/users",
        params={"plan": plan},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
