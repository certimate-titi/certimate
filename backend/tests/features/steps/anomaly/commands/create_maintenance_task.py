"""When 使用者建立維修任務（DataTable） — Command (POST)"""

from behave import when


@when('使用者 "{email}" 建立維修任務：')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    body = {}
    for row in context.table:
        field = row["欄位"]
        value = row["值"]
        if field == "estimated_hours":
            body[field] = float(value)
        else:
            body[field] = value

    response = context.api_client.post(
        "/api/v1/admin/maintenance-tasks",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    context.last_response = response
