"""When 使用者查看訂閱分布統計 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看訂閱分布統計')
def step_impl(context, email):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    response = context.api_client.get(
        "/api/v1/admin/finance/subscription-distribution",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
