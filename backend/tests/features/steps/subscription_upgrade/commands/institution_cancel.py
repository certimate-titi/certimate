"""When 機構管理員取消 ULTRA 訂閱且到期日已過 — Command"""

from behave import when


@when('機構 {inst_id:d} 的管理員取消 ULTRA 訂閱且到期日已過')
def step_impl(context, inst_id):
    admin_email = context.memo.get(f"institution_{inst_id}_admin_email")
    if admin_email and admin_email in context.ids:
        token = context.jwt_helper.generate_token(context.ids[admin_email])
    else:
        token = context.jwt_helper.generate_token(list(context.ids.values())[0])

    response = context.api_client.post(
        f"/api/v1/b2b/institutions/{inst_id}/cancel-subscription",
        headers={"Authorization": f"Bearer {token}"},
        json={"expired": True},
    )
    context.last_response = response
