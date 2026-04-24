"""Given 使用者已上傳資源且有 N 個分塊。"""

import tempfile
import uuid
from pathlib import Path

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

    # 建立實體 PDF 檔案供 DocumentProcessingService 解析
    temp_dir = Path(tempfile.gettempdir()) / "certimate_test_resources"
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_dir / f"{uuid.uuid4()}_{filename}"
    import fitz  # PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "測試 PDF 內容：這是一份提供 BDD 測試使用的範例文件。" * 5)
    doc.save(str(file_path))
    doc.close()

    resource = Resource(
        user_id=uuid.UUID(user_id),
        name=filename,
        type="pdf",
        status="COMPLETED",
        subject_id=uuid.UUID(subject_uuid),
        file_size_bytes=1024 * 1024,
        gcs_path=str(file_path),
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
