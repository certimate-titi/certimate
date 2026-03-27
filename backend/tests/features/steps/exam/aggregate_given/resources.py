"""Given 系統中有以下資源 — Aggregate Given"""

import uuid

from behave import given

from app.models.resource import Resource, ResourceStatus
from app.models.subject import Subject, SubjectCategory
from app.repositories.resource_repository import ResourceRepository
from app.repositories.subject_repository import SubjectRepository, SubjectCategoryRepository


@given('系統中有以下資源：')
def step_impl(context):
    db = context.db_session
    resource_repo = ResourceRepository(db)
    subject_repo = SubjectRepository(db)
    cat_repo = SubjectCategoryRepository(db)

    # 確保有一個預設科目（資源需要 subject_id）
    if "default_subject" not in context.ids:
        cat = SubjectCategory(name="預設分類")
        cat_repo.save(cat)
        subject = Subject(name="預設科目", category_id=cat.id)
        subject_repo.save(subject)
        context.ids["default_subject"] = str(subject.id)

    default_subject_id = uuid.UUID(context.ids["default_subject"])

    status_map = {
        "COMPLETED": ResourceStatus.COMPLETED,
        "PENDING": ResourceStatus.PENDING,
        "PROCESSING": ResourceStatus.PROCESSING,
        "FAILED": ResourceStatus.FAILED,
    }

    for row in context.table:
        resource_id_int = int(row["資源 ID"])
        user_id_key = row["使用者 ID"]
        name = row["名稱"]
        status_str = row["狀態"]

        # 找到使用者 ID
        if user_id_key not in context.ids:
            raise KeyError(f"找不到使用者 ID '{user_id_key}'")
        user_id = uuid.UUID(context.ids[user_id_key])

        # 判斷資源類型
        if name.endswith(".pdf"):
            res_type = "pdf"
        elif name.endswith(".md"):
            res_type = "markdown"
        else:
            res_type = "pdf"

        resource = Resource(
            id=uuid.UUID(int=resource_id_int),
            user_id=user_id,
            subject_id=default_subject_id,
            name=name,
            type=res_type,
            status=status_map.get(status_str, ResourceStatus.COMPLETED),
        )
        resource_repo.save(resource)
        context.ids[f"resource_{resource_id_int}"] = str(resource.id)
