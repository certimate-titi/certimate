"""Then 資源的狀態應為 — Aggregate Then"""

import uuid

from behave import then

from app.models.resource import Resource


@then('資源 {resource_id:d} 的狀態應為 "{expected_status}"')
def step_impl(context, resource_id, expected_status):
    db = context.db_session
    res_uuid = uuid.UUID(int=resource_id)

    resource = db.query(Resource).filter_by(id=res_uuid).first()
    db.refresh(resource)
    actual = resource.status.value if hasattr(resource.status, 'value') else str(resource.status)
    assert actual == expected_status, \
        f"預期資源狀態 '{expected_status}'，實際 '{actual}'"
