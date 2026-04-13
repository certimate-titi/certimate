"""Given 系統中有 seed 資源且有 N 個分塊。"""

import uuid

from behave import given

from app.models.resource import Resource
from app.models.resource_chunk import ResourceChunk


SEED_USER_ID = "00000000-0000-0000-0000-000000000001"


@given('系統中有 seed 資源 "{name}"（科目 ID: {subject_id:d}）且有 {chunk_count:d} 個分塊')
def step_impl(context, name, subject_id, chunk_count):
    db = context.db_session

    subject_uuid = context.ids.get(f"subject_{subject_id}")
    assert subject_uuid is not None, f"找不到科目 ID {subject_id}"

    # Ensure seed user exists
    from app.models.user import User
    seed_user = db.query(User).filter(User.id == uuid.UUID(SEED_USER_ID)).first()
    if seed_user is None:
        seed_user = User(
            id=uuid.UUID(SEED_USER_ID),
            email="seed@system.local",
            password_hash="not-a-real-hash",
            display_name="System Seed",
        )
        db.add(seed_user)
        db.commit()

    resource = Resource(
        user_id=uuid.UUID(SEED_USER_ID),
        name=name,
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
            content=f"Seed 分塊 {i + 1}：{name}",
            token_count=80,
        )
        db.add(chunk)

    db.commit()

    context.memo["seed_resource_id"] = str(resource.id)
