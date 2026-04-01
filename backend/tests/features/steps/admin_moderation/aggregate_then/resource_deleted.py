"""Then 目標資源應被刪除 — Aggregate Then"""

import uuid

from behave import then

from app.models.resource import Resource, ResourceStatus


@then('目標資源 {target_id} 應被刪除')
def step_impl(context, target_id):
    db = context.db_session
    db.expire_all()

    resource_id_str = context.ids.get(f"resource_{target_id}")
    assert resource_id_str, f"找不到 resource_{target_id} 的 UUID 映射"

    resource = db.query(Resource).filter(
        Resource.id == uuid.UUID(resource_id_str)
    ).first()

    assert resource is not None, f"找不到資源 {target_id}"
    status_val = resource.status.value if hasattr(resource.status, "value") else str(resource.status)
    assert status_val == "DELETED", \
        f"資源 {target_id} 的狀態應為 'DELETED'，實際 '{status_val}'"
