"""When 上傳 PDF：multipart 主流程（取代 legacy /resources/upload）。"""

from behave import when


@when('使用者 "{email}" 上傳 PDF 檔案 "{filename}"，大小為 {size:d}MB，科目為 {subject_id:d}')
def step_impl(context, email, filename, size, subject_id):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    # 產生 size MB 的 fake bytes（足以觸發實際 plan-limit 檢查）
    payload = b"%PDF-1.4\n" + b"\x00" * (size * 1024 * 1024 - 9) if size > 0 else b""

    response = context.api_client.post(
        "/api/v1/resources/upload-file",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, payload, "application/pdf")},
        data={
            "subject_id": subject_uuid or "",
            "filename": filename,
            "resource_type": "pdf",
        },
    )
    context.last_response = response
