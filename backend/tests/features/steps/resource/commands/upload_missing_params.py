"""When 上傳缺少 file / subject_id 欄位（驗 422）— multipart 主流程。"""

from behave import when


@when('使用者 "{email}" 上傳檔案 ，科目為 {subject_id:d}')
def step_upload_missing_file(context, email, subject_id):
    """缺 file → 422。"""
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    # 不提供 files → FastAPI 422
    response = context.api_client.post(
        "/api/v1/resources/upload-file",
        headers={"Authorization": f"Bearer {token}"},
        data={"subject_id": subject_uuid or ""},
    )
    context.last_response = response


@when('使用者 "{email}" 上傳檔案 {filename}，科目為 ')
def step_upload_missing_subject(context, email, filename):
    """缺 subject_id → 422。"""
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/resources/upload-file",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, b"%PDF-1.4\n" + b"\x00" * 1023, "application/pdf")},
        # 不送 subject_id → FastAPI 422
    )
    context.last_response = response
