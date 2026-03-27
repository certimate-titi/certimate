"""When 使用者更新 Feature Flag — Command"""

from behave import when


@when('使用者 "{email}" 更新 Feature Flag {flag_id:d}，上線比例為 {percentage:d}，目標方案為 "{target_plans}"')
def step_impl(context, email, flag_id, percentage, target_plans):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    flag_uuid = context.ids.get(f"flag_{flag_id}")

    response = context.api_client.put(
        f"/api/v1/admin/system-settings/feature-flags/{flag_uuid}",
        json={
            "enabled": True,
            "rollout_percentage": percentage,
            "target_plans": target_plans,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
