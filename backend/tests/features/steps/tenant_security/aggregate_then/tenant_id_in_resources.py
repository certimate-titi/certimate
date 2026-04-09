"""Then resources 表中該筆資料的 tenant_id 應等於 {slug} 的 UUID."""

from behave import then
import uuid


@then('resources 表中該筆資料的 tenant_id 應等於 {slug} 的 UUID')
def step_impl(context, slug):
    """驗證 resources 表中的 tenant_id 等於指定租戶的 UUID。"""
    from app.models.resource import Resource

    tenant_id = context.ids.get(slug)
    assert tenant_id, f"找不到租戶 '{slug}' 的 UUID"

    resource_id = context.ids.get("uploaded_resource")
    if resource_id:
        resource = context.db_session.query(Resource).filter(
            Resource.id == uuid.UUID(resource_id)
        ).first()
        assert resource is not None, "找不到已上傳的 resource"
        assert str(resource.tenant_id) == tenant_id, \
            f"tenant_id 不符：期望 {tenant_id}，實際 {resource.tenant_id}"
    else:
        # 驗證最近上傳的 resource（依建立時間排序）
        resource = context.db_session.query(Resource).order_by(
            Resource.created_at.desc()
        ).first()
        assert resource is not None, "找不到任何 resource"
        assert str(resource.tenant_id) == tenant_id, \
            f"tenant_id 不符：期望 {tenant_id}，實際 {resource.tenant_id}"
