"""When 使用者更新維修任務狀態 — Command (PUT)"""

from behave import when


@when('使用者 "{email}" 更新維修任務 "{task_id}" 的狀態為 "{status}"')
def step_impl(context, email, task_id, status):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.put(
        f"/api/v1/admin/maintenance-tasks/{task_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": status},
    )
    context.last_response = response
