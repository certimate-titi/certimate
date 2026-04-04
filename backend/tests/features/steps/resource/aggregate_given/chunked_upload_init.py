from behave import given
import uuid


@given('使用者 "{email}" 已初始化分片上傳任務，總共 {total_chunks:d} 片')
def step_impl(context, email, total_chunks):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    # Store chunked upload metadata in context.memo for subsequent steps
    upload_id = str(uuid.uuid4())
    context.memo["upload_id"] = upload_id
    context.memo["total_chunks"] = total_chunks
    context.memo["uploaded_chunks"] = 0
    context.memo["chunked_upload_user_email"] = email

    # Also register in ChunkedUploadService's in-memory store
    from app.services.chunked_upload_service import _uploads, UPLOAD_DIR
    chunk_dir = UPLOAD_DIR / upload_id
    chunk_dir.mkdir(parents=True, exist_ok=True)
    _uploads[upload_id] = {
        "user_id": user_id,
        "filename": "test_chunked.pdf",
        "file_size": total_chunks * 5 * 1024 * 1024,
        "total_chunks": total_chunks,
        "uploaded_chunks": set(),
        "chunk_dir": str(chunk_dir),
        "subject_id": None,
    }
