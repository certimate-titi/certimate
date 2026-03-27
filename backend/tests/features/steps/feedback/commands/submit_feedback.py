"""When 使用者 "..." 提交意見反饋：(with table) — Command (POST)"""

from behave import when


FIELD_MAP = {
    "類型": "type",
    "主旨": "subject",
    "內容": "content",
}


@when('使用者 "{email}" 提交意見反饋：')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    payload = {}
    for row in context.table:
        field_name = row["欄位"]
        field_key = FIELD_MAP.get(field_name, field_name)
        payload[field_key] = row["值"]

    response = context.api_client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    context.last_response = response
