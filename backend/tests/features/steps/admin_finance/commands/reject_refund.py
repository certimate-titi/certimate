"""When 使用者駁回退款 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 駁回退款 "{refund_id}"，理由為 "{reason}"')
def step_impl(context, email, refund_id, reason):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    response = context.api_client.post(
        f"/api/v1/admin/finance/refunds/{refund_id}/reject",
        json={"reason": reason},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
