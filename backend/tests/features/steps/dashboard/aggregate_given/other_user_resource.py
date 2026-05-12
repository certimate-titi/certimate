"""Given 他使用者在同科目上傳資源 — Aggregate Given（dashboard ownership isolation）"""

import uuid

from behave import given

from app.models.resource import Resource, ResourceStatus
from app.repositories.resource_repository import ResourceRepository


@given('使用者 "{email}" 在科目 "{subject_name}" 上傳了一份資源，ID 存為 "{memo_key}"')
def step_impl(context, email, subject_name, memo_key):
    db = context.db_session
    repo = ResourceRepository(db)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    subject_key = f"subject_{subject_name}"
    if subject_key not in context.ids:
        raise KeyError(f"找不到科目 '{subject_name}' 的 ID（預期 key={subject_key}）")

    user_id = uuid.UUID(context.ids[email])
    subject_id = uuid.UUID(context.ids[subject_key])

    resource = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name=f"{email}_resource",
        type="pdf",
        status=ResourceStatus.COMPLETED,
    )
    repo.save(resource)
    context.ids[memo_key] = str(resource.id)
