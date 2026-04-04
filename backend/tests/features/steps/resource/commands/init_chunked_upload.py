from behave import when


@when('使用者 "{email}" 初始化分片上傳，檔案名稱為 "{filename}"，大小為 {size:d}MB，科目為 {subject_id:d}')
def step_impl(context, email, filename, size, subject_id):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    response = context.api_client.post(
        "/api/v1/resources/chunked-upload/init",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filename": filename,
            "subject_id": subject_uuid,
            "file_size_mb": size,
        },
    )
    context.last_response = response
