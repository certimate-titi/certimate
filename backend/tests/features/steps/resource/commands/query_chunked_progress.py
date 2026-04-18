from behave import when


@when('使用者 "{email}" 查詢分片上傳進度')
def step_impl(context, email):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    upload_id = context.memo.get("upload_id")
    assert upload_id is not None, "找不到分片上傳任務 ID"

    response = context.api_client.get(
        f"/api/v1/resources/chunked/{upload_id}/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
