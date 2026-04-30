"""租戶 "{slug}" 已上傳資源並建立了 {count} 個 chunks."""

import uuid
from behave import given
from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope
from app.models.resource_chunk import ResourceChunk
from app.models.subject import Subject


@given('租戶 "{slug}" 已上傳資源並建立了 {count:d} 個 chunks（tenant_id = {slug2}）')
def step_impl(context, slug, count, slug2):
    """為指定租戶建立 resource 和 resource_chunks（帶 tenant_id）。"""
    tenant_id = uuid.UUID(context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}"))
    user_id = uuid.UUID(context.ids.get(f"user_{slug}"))

    # 建立一個 subject（需要關聯）
    subject_key = f"subject_{slug}"
    if subject_key not in context.ids:
        from app.models.subject import SubjectCategory
        category = context.db_session.query(SubjectCategory).first()
        if category is None:
            category = SubjectCategory(name="Test Category")
            context.db_session.add(category)
            context.db_session.commit()
            context.db_session.refresh(category)
        subject = Subject(
            id=uuid.uuid4(),
            name=f"Subject for {slug}",
            category_id=category.id,
        )
        context.db_session.merge(subject)
        context.db_session.commit()
        context.ids[subject_key] = str(subject.id)
    subject_id = uuid.UUID(context.ids[subject_key])

    # 建立 resource
    resource = Resource(
        id=uuid.uuid4(),
        user_id=user_id,
        subject_id=subject_id,
        name=f"Test Resource for {slug}",
        type=ResourceType.PDF,
        scope=ResourceScope.PERSONAL,
        status=ResourceStatus.COMPLETED,
        tenant_id=tenant_id,
    )
    context.db_session.merge(resource)
    context.db_session.commit()
    context.ids[f"resource_{slug}"] = str(resource.id)

    # 建立 N 個 chunks
    for i in range(count):
        chunk = ResourceChunk(
            id=uuid.uuid4(),
            resource_id=resource.id,
            chunk_index=i,
            content=f"Chunk {i} for {slug}",
            token_count=100,
            tenant_id=tenant_id,
        )
        context.db_session.add(chunk)
    context.db_session.commit()

    context.memo[f"chunk_count_{slug}"] = count
