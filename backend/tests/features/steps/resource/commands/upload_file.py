"""When 上傳檔案（缺欄位驗證主用 — multipart）。"""

from behave import when


@when('使用者 "{email}" 上傳檔案 "{filename}"，科目為 {subject_id:d}')
def step_impl(context, email, filename, subject_id):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    response = context.api_client.post(
        "/api/v1/resources/upload-file",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename or "", b"%PDF-1.4\n" + b"\x00" * 1023, "application/pdf")},
        data={
            "subject_id": subject_uuid or "",
            "filename": filename,
            "resource_type": "pdf",
        },
    )
    context.last_response = response
