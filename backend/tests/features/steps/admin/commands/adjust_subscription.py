"""When 使用者調整某使用者的訂閱方案 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 將使用者 {user_key} 的訂閱方案調整為 "{plan}"，OTP 為 "{otp}"')
def step_impl(context, email, user_key, plan, otp):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    target_id = context.ids.get(user_key.strip())

    response = context.api_client.post(
        f"/api/v1/admin/users/{target_id}/adjust-subscription",
        json={"plan": plan, "otp": otp},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
