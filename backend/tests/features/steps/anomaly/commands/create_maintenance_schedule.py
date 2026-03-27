"""When 使用者建立維修排程 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 建立維修排程：')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    body = {}
    for row in context.table:
        field = row["欄位"]
        value = row["值"]
        body[field] = value

    response = context.api_client.post(
        "/api/v1/admin/maintenance-schedules",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    context.last_response = response
