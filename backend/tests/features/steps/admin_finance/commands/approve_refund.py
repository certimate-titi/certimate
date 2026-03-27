"""When 使用者核准退款 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 核准退款 "{refund_id}"')
def step_impl(context, email, refund_id):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    response = context.api_client.post(
        f"/api/v1/admin/finance/refunds/{refund_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
