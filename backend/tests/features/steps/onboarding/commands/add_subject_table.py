"""When 使用者新增備考科目（表格格式）— Command (POST)"""

from behave import when


@when('使用者 "{email}" 新增備考科目：')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    data = {}
    for row in context.table:
        data[row["欄位"]] = row["值"]

    response = context.api_client.post(
        "/api/v1/subjects",
        headers={"Authorization": f"Bearer {token}"},
        json=data,
    )
    context.last_response = response
