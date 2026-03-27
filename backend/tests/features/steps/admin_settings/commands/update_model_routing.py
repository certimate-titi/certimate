"""When 使用者更新 AI 模型路由 — Command"""

from behave import when


@when('使用者 "{email}" 更新 AI 模型路由，方案為 "{plan}"，任務類型為 "{task_type}"，主要模型為 "{primary_model}"')
def step_impl(context, email, plan, task_type, primary_model):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.put(
        f"/api/v1/admin/system-settings/model-routing/{plan}/{task_type}",
        json={"primary_model": primary_model},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
