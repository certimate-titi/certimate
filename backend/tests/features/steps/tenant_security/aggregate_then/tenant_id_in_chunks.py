"""Then resource_chunks 表中該資源的所有 chunks 的 tenant_id 亦應等於 {slug} 的 UUID."""

from behave import then
import uuid


@then('resource_chunks 表中該資源的所有 chunks 的 tenant_id 亦應等於 {slug} 的 UUID')
def step_impl(context, slug):
    """驗證 resource_chunks 的 tenant_id 等於指定租戶的 UUID。"""
    from app.models.resource_chunk import ResourceChunk

    tenant_id = context.ids.get(slug)
    assert tenant_id, f"找不到租戶 '{slug}' 的 UUID"

    resource_id = context.ids.get("uploaded_resource")
    if resource_id:
        chunks = context.db_session.query(ResourceChunk).filter(
            ResourceChunk.resource_id == uuid.UUID(resource_id)
        ).all()
    else:
        chunks = context.db_session.query(ResourceChunk).all()

    assert len(chunks) > 0, "找不到任何 resource_chunks"
    for chunk in chunks:
        assert str(chunk.tenant_id) == tenant_id, \
            f"chunk {chunk.id} 的 tenant_id 不符：期望 {tenant_id}，實際 {chunk.tenant_id}"
