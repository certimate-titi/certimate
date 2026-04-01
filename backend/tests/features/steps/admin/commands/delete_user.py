"""When 使用者刪除使用者 N 的帳號（需確認名稱） — Command (POST)"""

from behave import when


@when('使用者 "{email}" 刪除使用者 {user_key} 的帳號，確認名稱為 "{confirm_name}"')
def step_impl(context, email, user_key, confirm_name):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    target_id = context.ids.get(user_key.strip())

    response = context.api_client.post(
        "/api/v1/admin/users/delete",
        json={"target_user_id": target_id, "confirm_name": confirm_name},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
