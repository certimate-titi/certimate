"""When 使用者新增管理員 — Command"""

from behave import when


@when('使用者 "{email}" 新增管理員，Email 為 "{target_email}"，角色為 "{role}"')
def step_impl(context, email, target_email, role):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    payload = {
        "target_email": target_email,
        "role": role,
    }

    response = context.api_client.post(
        "/api/v1/admin/system-settings/admins",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
