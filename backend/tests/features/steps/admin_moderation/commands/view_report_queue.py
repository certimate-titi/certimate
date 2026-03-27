"""When 使用者查看內容檢舉佇列 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看內容檢舉佇列，篩選狀態為 "{status}"')
def step_impl(context, email, status):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    response = context.api_client.get(
        f"/api/v1/admin/moderation/reports?status={status}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
