"""Given FAILED 狀態的資源（含 error_message）。"""

import uuid
from behave import given

from app.models.resource import Resource


@given('使用者 "{email}" 有一筆 status=FAILED 的資源，error_message 為「{msg}」')
def step_impl(context, email, msg):
    db = context.db_session
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    from app.models.subject import Subject
    subj = db.query(Subject).first()
    if subj is None:
        subj = Subject(name="測試科目", category="test")
        db.add(subj)
        db.commit()

    resource = Resource(
        user_id=uuid.UUID(user_id),
        name="failed.pdf",
        type="pdf",
        status="FAILED",
        subject_id=subj.id,
        file_size_bytes=1024,
        error_message=msg,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    context.memo["last_resource_id"] = str(resource.id)
    context.memo["expected_error_message"] = msg
