"""When 使用者更新異常狀態 — Command (PUT)"""

from behave import when


@when('使用者 "{email}" 更新異常 "{error_id}"，狀態為 "{status}"，指派給 "{assigned_to}"')
def step_impl(context, email, error_id, status, assigned_to):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.put(
        f"/api/v1/admin/anomalies/{error_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "status": status,
            "assigned_to": assigned_to,
        },
    )
    context.last_response = response
