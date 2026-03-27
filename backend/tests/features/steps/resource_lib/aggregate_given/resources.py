"""Given 系統中有以下資源庫資源 — Aggregate Given"""

import uuid

from behave import given

from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope
from app.models.subject import SubjectCategory, Subject


TYPE_MAP = {
    "pdf": ResourceType.PDF,
    "markdown": ResourceType.MARKDOWN,
    "youtube": ResourceType.YOUTUBE,
    "image": ResourceType.IMAGE,
    "txt": ResourceType.TXT,
}

STATUS_MAP = {
    "COMPLETED": ResourceStatus.COMPLETED,
    "FAILED": ResourceStatus.FAILED,
    "PENDING": ResourceStatus.PENDING,
    "PROCESSING": ResourceStatus.PROCESSING,
}


@given('系統中有以下資源庫資源：')
def step_impl(context):
    db = context.db_session

    # Create default subject if needed
    if "default_cat" not in context.ids:
        cat = SubjectCategory(name="default_cat")
        db.add(cat)
        db.flush()
        context.ids["default_cat"] = str(cat.id)

    if "default_subject" not in context.ids:
        cat_id = uuid.UUID(context.ids["default_cat"])
        subj = Subject(name="default", category_id=cat_id)
        db.add(subj)
        db.flush()
        context.ids["default_subject"] = str(subj.id)

    subject_id = uuid.UUID(context.ids["default_subject"])

    for row in context.table:
        res_id = int(row["資源 ID"])
        user_id_key = row["使用者 ID"].strip()
        name = row["名稱"]
        type_raw = row["類型"].lower()
        status_raw = row["狀態"]

        user_uuid = uuid.UUID(context.ids[user_id_key])

        res = Resource(
            id=uuid.UUID(int=res_id),
            user_id=user_uuid,
            subject_id=subject_id,
            name=name,
            type=TYPE_MAP.get(type_raw, ResourceType.PDF),
            status=STATUS_MAP.get(status_raw, ResourceStatus.COMPLETED),
            scope=ResourceScope.PERSONAL,
        )
        db.add(res)
        db.flush()
        context.ids[f"resource_{res_id}"] = str(res.id)

    db.commit()
