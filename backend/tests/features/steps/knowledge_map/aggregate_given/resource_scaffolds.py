"""Given 資源有以下學習鷹架（TASK-02）— Aggregate Given"""

import uuid

from behave import given

from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType


@given('資源 "{resource_name}" 有以下學習鷹架：')
def step_impl(context, resource_name):
    db = context.db_session
    resource = (
        db.query(Resource).filter(Resource.name == resource_name).first()
    )
    if resource is None:
        raise AssertionError(f"找不到資源 '{resource_name}'")

    for row in context.table:
        heading = row["chapter_heading"]
        raw_type = row["type"]
        t = ResourceScaffoldType(raw_type)

        def _int_or_none(v: str) -> int | None:
            v = (v or "").strip()
            return int(v) if v and v.lower() != "null" else None

        scaffold = ResourceScaffold(
            id=uuid.uuid4(),
            resource_id=resource.id,
            tenant_id=resource.tenant_id,
            chapter_heading=heading,
            type=t.value,
            content=row["content"],
            page_start=_int_or_none(row["page_start"]),
            page_end=_int_or_none(row["page_end"]),
        )
        db.add(scaffold)
    db.commit()
