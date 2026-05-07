"""When 上傳影像檔（multipart 主流程）。"""

from behave import when


@when('使用者 "{email}" 上傳影像檔案 "{filename}"，大小為 {size:d}MB，科目為 {subject_id:d}')
def step_impl(context, email, filename, size, subject_id):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * (size * 1024 * 1024 - 8) if size > 0 else b""

    response = context.api_client.post(
        "/api/v1/resources/upload-file",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, payload, "image/png")},
        data={
            "subject_id": subject_uuid or "",
            "filename": filename,
            "resource_type": "image",
        },
    )
    context.last_response = response
