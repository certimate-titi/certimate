"""When 使用者上傳單一分片 — Command"""

import io

from behave import when


@when('使用者 "{email}" 上傳第 {chunk_index:d} 片（大小為 {size:d} bytes）')
def step_impl_upload_chunk(context, email, chunk_index, size):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"
    upload_id = context.memo.get("upload_id")
    assert upload_id, "memo 無 upload_id（先執行「已初始化分片上傳」的 Given）"

    token = context.jwt_helper.generate_token(user_id)
    chunk_data = b"x" * size
    response = context.api_client.post(
        f"/api/v1/resources/chunked/{upload_id}/chunk/{chunk_index}",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (f"chunk-{chunk_index}.bin", io.BytesIO(chunk_data), "application/octet-stream")},
    )
    context.last_response = response
