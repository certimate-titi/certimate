"""Then 資源 status / error_message 驗證。"""

import uuid
from behave import then

from app.models.resource import Resource


def _reload_resource(context) -> Resource:
    db = context.db_session
    resource_id = context.memo.get("last_resource_id")
    assert resource_id, "找不到 last_resource_id"
    db.expire_all()
    resource = db.query(Resource).filter(Resource.id == uuid.UUID(resource_id)).first()
    assert resource is not None, f"找不到 Resource id={resource_id}"
    return resource


@then('該資源的 status 應為 FAILED')
def step_impl_status(context):
    resource = _reload_resource(context)
    status_val = resource.status.value if hasattr(resource.status, 'value') else resource.status
    assert status_val == "FAILED", f"預期 status=FAILED，實際={status_val}"


@then('該資源的 error_message 應以「{prefix}」開頭')
def step_impl_error_prefix(context, prefix):
    resource = _reload_resource(context)
    msg = resource.error_message or ""
    assert msg.startswith(prefix), f"預期 error_message 以「{prefix}」開頭，實際={msg!r}"
