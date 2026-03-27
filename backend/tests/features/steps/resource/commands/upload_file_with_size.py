from behave import when


@when('使用者 "{email}" 上傳大小為 {size:d}MB 的 PDF 檔案 "{filename}"，科目為 {subject_id:d}')
def step_impl(context, email, size, filename, subject_id):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    response = context.api_client.post(
        "/api/v1/resources/upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filename": filename,
            "subject_id": subject_uuid,
            "file_size_mb": size,
            "type": "pdf",
        },
    )
    context.last_response = response
