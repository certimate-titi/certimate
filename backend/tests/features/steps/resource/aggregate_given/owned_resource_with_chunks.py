"""Given 使用者 "{email}" 在科目 "{subject_alias}" 擁有資源 "{res_alias}" 名稱 "{name}"，含 N 個 chunk"""

import uuid

from behave import given

from app.models.resource import Resource, ResourceStatus
from app.models.resource_chunk import ResourceChunk


@given('使用者 "{email}" 在科目 "{subject_alias}" 擁有資源 "{res_alias}" 名稱 "{name}"，含 {chunk_count:d} 個 chunk')
def step_impl(context, email, subject_alias, res_alias, name, chunk_count):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    subject_id = uuid.UUID(context.ids[subject_alias])

    rid = uuid.uuid4()
    resource = Resource(
        id=rid,
        user_id=user_id,
        subject_id=subject_id,
        name=name,
        type="pdf",
        scope="personal",
        status=ResourceStatus.COMPLETED.value,
    )
    db.add(resource)
    db.flush()

    for i in range(chunk_count):
        chunk = ResourceChunk(
            id=uuid.uuid4(),
            resource_id=rid,
            chunk_index=i,
            content=f"chunk-{i}-content",
            token_count=10,
        )
        db.add(chunk)

    db.commit()
    context.ids[res_alias] = str(rid)
