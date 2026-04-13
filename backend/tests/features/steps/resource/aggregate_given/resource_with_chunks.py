"""Given 使用者已上傳資源且有 N 個分塊。"""

import uuid

from behave import given

from app.models.resource import Resource
from app.models.resource_chunk import ResourceChunk


@given('使用者 "{email}" 已上傳資源 "{filename}"（科目 ID: {subject_id:d}）且有 {chunk_count:d} 個分塊')
def step_impl(context, email, filename, subject_id, chunk_count):
    db = context.db_session
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    subject_uuid = context.ids.get(f"subject_{subject_id}")
    assert subject_uuid is not None, f"找不到科目 ID {subject_id}"

    resource = Resource(
        user_id=uuid.UUID(user_id),
        name=filename,
        type="pdf",
        status="COMPLETED",
        subject_id=uuid.UUID(subject_uuid),
        file_size_bytes=1024 * 1024,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    for i in range(chunk_count):
        chunk = ResourceChunk(
            resource_id=resource.id,
            chunk_index=i,
            content=f"第 {i + 1} 段內容：{filename} 的分塊",
            token_count=100,
        )
        db.add(chunk)

    db.commit()

    context.memo["last_resource_id"] = str(resource.id)
