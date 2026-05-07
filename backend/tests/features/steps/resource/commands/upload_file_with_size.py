"""When 上傳特定 size 的 PDF（plan-limit 驗證 — multipart 真實 bytes）。"""

from behave import when


@when('使用者 "{email}" 上傳大小為 {size:d}MB 的 PDF 檔案 "{filename}"，科目為 {subject_id:d}')
def step_impl(context, email, size, filename, subject_id):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    # 產生 size MB 的真實 bytes，觸發 plan-quota 邏輯（FREE 10MB / PRO 50MB / ULTRA 100MB）
    payload = b"%PDF-1.4\n" + b"\x00" * (size * 1024 * 1024 - 9)

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
