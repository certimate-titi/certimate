"""Given 使用者本月已完成 N 次 LLM 資源解析 — EPIC-035 配額."""

import uuid

from behave import given

from app.models.resource import Resource
from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob


@given('使用者 "{email}" 本月已完成 {count:d} 次 LLM 資源解析')
def step_impl(context, email, count):
    db = context.db_session
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"
    subject_uuid = context.ids.get("subject_1")
    assert subject_uuid is not None, "找不到 subject_1"

    for i in range(count):
        res = Resource(
            user_id=uuid.UUID(user_id),
            name=f"配額已用 {i+1}.pdf",
            type="pdf",
            status="COMPLETED",
            subject_id=uuid.UUID(subject_uuid),
            file_size_bytes=1024,
        )
        db.add(res)
        db.flush()
        db.add(ResourceParseJob(
            resource_id=res.id,
            tenant_id=res.tenant_id,
            status=ParseJobStatus.SUCCESS.value,
        ))
    db.commit()
