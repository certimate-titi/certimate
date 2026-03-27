"""When 使用者更新方案限額 — Command"""

from behave import when


@when('使用者 "{email}" 更新方案限額，方案為 "{plan}"，每月上傳數為 {count:d}')
def step_impl(context, email, plan, count):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.put(
        f"/api/v1/admin/system-settings/plan-quota/{plan}",
        json={"monthly_uploads": count},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
