from behave import given
import uuid


@given('使用者 "{email}" 已上傳所有 {total_chunks:d} 片')
def step_impl(context, email, total_chunks):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    # Initialize chunked upload context
    upload_id = context.memo.get("upload_id") or str(uuid.uuid4())
    context.memo["upload_id"] = upload_id
    context.memo["total_chunks"] = total_chunks
    context.memo["uploaded_chunks"] = total_chunks
    context.memo["chunked_upload_user_email"] = email

    # Register in ChunkedUploadService's in-memory store with all chunks uploaded
    from app.services.chunked_upload_service import _uploads, UPLOAD_DIR
    chunk_dir = UPLOAD_DIR / upload_id
    chunk_dir.mkdir(parents=True, exist_ok=True)
    # 建立實體 chunk 檔案讓 merge 能讀取
    for i in range(total_chunks):
        chunk_file = chunk_dir / f"chunk_{i:05d}"
        chunk_file.write_bytes(b"x" * 1024)
    # Ensure a subject exists for the resource
    from app.models.subject import Subject
    db = context.db_session
    subj = db.query(Subject).first()
    subject_id = str(subj.id) if subj else None
    if not subject_id:
        import uuid as _uuid
        subj = Subject(name="測試科目", category="test")
        db.add(subj)
        db.commit()
        subject_id = str(subj.id)

    _uploads[upload_id] = {
        "user_id": user_id,
        "filename": "test_chunked.pdf",
        "file_size": 300 * 1024 * 1024,  # 300MB
        "total_chunks": total_chunks,
        "uploaded_chunks": set(range(total_chunks)),
        "chunk_dir": str(chunk_dir),
        "subject_id": subject_id,
    }
