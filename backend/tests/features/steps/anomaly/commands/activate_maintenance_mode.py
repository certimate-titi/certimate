"""When 使用者啟動全站維修模式 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 啟動全站維修模式，原因為 "{reason}"，預計恢復時間為 "{estimated_recovery}"')
def step_impl(context, email, reason, estimated_recovery):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/admin/maintenance-mode",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "reason": reason,
            "estimated_recovery": estimated_recovery,
        },
    )
    context.last_response = response
