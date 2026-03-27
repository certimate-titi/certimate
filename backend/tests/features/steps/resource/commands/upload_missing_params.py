from behave import when


@when('使用者 "{email}" 上傳檔案 ，科目為 {subject_id:d}')
def step_upload_missing_file(context, email, subject_id):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    response = context.api_client.post(
        "/api/v1/resources/upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filename": None,
            "subject_id": subject_uuid,
        },
    )
    context.last_response = response


@when('使用者 "{email}" 上傳檔案 {filename}，科目為 ')
def step_upload_missing_subject(context, email, filename):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/resources/upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filename": filename,
            "subject_id": None,
        },
    )
    context.last_response = response
