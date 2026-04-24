"""When 上傳特殊 PDF（損毀 / 版權 / 無文字）。"""

import io
import uuid
from behave import when


def _get_user_token(context, email):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"
    return user_id, context.jwt_helper.create_token(user_id)


def _get_subject_id(context):
    from app.models.subject import Subject
    db = context.db_session
    subj = db.query(Subject).first()
    if subj is None:
        subj = Subject(name="測試科目", category="test")
        db.add(subj)
        db.commit()
    return str(subj.id)


def _upload_pdf(context, email, filename, pdf_bytes):
    user_id, token = _get_user_token(context, email)
    subject_id = _get_subject_id(context)
    response = context.api_client.post(
        "/api/v1/resources/upload-file",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, pdf_bytes, "application/pdf")},
        data={"subject_id": subject_id, "filename": filename, "resource_type": "pdf"},
    )
    context.last_response = response
    context.memo["uploader_user_id"] = user_id


@when('使用者 "{email}" 上傳損毀的 PDF 檔案「{filename}」')
def step_impl_corrupted(context, email, filename):
    _upload_pdf(context, email, filename, b"this is not a valid pdf at all")


@when('使用者 "{email}" 上傳前兩頁含「{keyword}」的 PDF')
def step_impl_copyright(context, email, keyword):
    # 用 CJK 字型插入中文關鍵字，以便 fitz.get_text() 能在預檢時辨識
    import fitz
    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page()
        # 以 ASCII 版權關鍵字保底（COPYRIGHT_KEYWORDS 含 "All Rights Reserved"、"Confidential"）
        page.insert_text((72, 72), "Test Document. All Rights Reserved. Confidential. Do Not Distribute.")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    _upload_pdf(context, email, "copyright.pdf", buf.getvalue())


from behave import given


@given('使用者 "{email}" 上傳一個無文字的 PDF 檔案')
def step_impl_no_text(context, email):
    """建立一個純空白（無文字）的 PDF Resource，繞過預檢以測試背景處理分類。"""
    import tempfile
    import uuid as _uuid
    from pathlib import Path
    import fitz
    from app.models.resource import Resource
    from app.models.subject import Subject

    db = context.db_session
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    subj = db.query(Subject).first()
    if subj is None:
        subj = Subject(name="測試科目", category="test")
        db.add(subj)
        db.commit()

    # 產生一個純空白 PDF（無任何文字）
    temp_dir = Path(tempfile.gettempdir()) / "certimate_test_resources"
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_dir / f"{_uuid.uuid4()}_blank.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(file_path))
    doc.close()

    resource = Resource(
        user_id=_uuid.UUID(user_id),
        name="blank.pdf",
        type="pdf",
        status="PENDING",
        subject_id=subj.id,
        file_size_bytes=file_path.stat().st_size,
        gcs_path=str(file_path),
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    context.memo["last_resource_id"] = str(resource.id)
    context.memo["uploader_user_id"] = user_id
