"""When 使用者 "..." 查看所有狀態為 "..." 的意見反饋 / 查看所有意見反饋清單 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看所有狀態為 "{status}" 的意見反饋')
def step_impl(context, email, status):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/feedback/admin/list",
        params={"status": status},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查看所有意見反饋清單')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/feedback/admin/list",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
