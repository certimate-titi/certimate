"""When 使用者更新個人資料 — Command (PATCH)"""

from behave import when


@when('使用者 "{email}" 更新個人資料：')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    payload = {}
    for row in context.table:
        field = row["欄位"]
        value = row["值"]
        # Convert numeric fields
        if field == "age":
            payload[field] = int(value)
        else:
            payload[field] = value

    response = context.api_client.patch(
        "/api/v1/dashboard/profile",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    context.last_response = response
