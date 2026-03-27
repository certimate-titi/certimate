"""When 使用者 "..." 提交意見反饋，缺少 ... — Command (POST)"""

from behave import when


FIELD_MAP = {
    "類型": "type",
    "主旨": "subject",
    "內容": "content",
}


@when('使用者 "{email}" 提交意見反饋，缺少 {missing_field}')
def step_impl(context, email, missing_field):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # Build a complete payload, then remove the missing field
    payload = {
        "type": "BUG",
        "subject": "測試主旨",
        "content": "測試內容描述",
    }

    field_key = FIELD_MAP.get(missing_field.strip())
    assert field_key is not None, f"未知的欄位名稱: {missing_field}"
    del payload[field_key]

    response = context.api_client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    context.last_response = response
