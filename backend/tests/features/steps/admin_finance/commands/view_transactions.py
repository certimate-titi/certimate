"""When 使用者查看交易紀錄 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看交易紀錄')
def step_impl(context, email):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    response = context.api_client.get(
        "/api/v1/admin/finance/transactions",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查看交易紀錄，篩選狀態為 "{status}"')
def step_impl_filter(context, email, status):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    response = context.api_client.get(
        f"/api/v1/admin/finance/transactions?status={status}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
