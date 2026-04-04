"""When 機構管理員將使用者從機構移除 — Command"""

from behave import when


@when('機構管理員將使用者 "{email}" 從機構 {inst_id:d} 移除')
def step_impl(context, email, inst_id):
    # 取得機構管理員的 JWT token
    admin_email = context.memo.get(f"institution_{inst_id}_admin_email")
    if admin_email and admin_email in context.ids:
        token = context.jwt_helper.generate_token(context.ids[admin_email])
    else:
        # Fallback: use the first available user token
        token = context.jwt_helper.generate_token(context.ids.get(email, ""))

    response = context.api_client.delete(
        f"/api/v1/b2b/institutions/{inst_id}/students/{email}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
