"""Given 他使用者在科目下建立資源 — Aggregate Given（Issue #74）"""

import uuid

from behave import given

from app.models.resource import Resource, ResourceStatus
from app.repositories.resource_repository import ResourceRepository

SEED_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@given('使用者 "{email}" 在科目 "{subject}" 下建立了資源 "{resource_name}"')
def step_impl(context, email, subject, resource_name):
    db = context.db_session
    repo = ResourceRepository(db)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")
    if subject not in context.ids:
        raise KeyError(f"找不到科目 '{subject}' 的 ID")

    user_id = uuid.UUID(context.ids[email])
    subject_id = uuid.UUID(context.ids[subject])

    resource = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name=resource_name,
        type="pdf",
        status=ResourceStatus.COMPLETED,
    )
    repo.save(resource)
    context.ids[resource_name] = str(resource.id)


@given('seed user 在科目 "{subject}" 下建立了預設資源 "{resource_name}"')
def step_seed_resource(context, subject, resource_name):
    db = context.db_session
    repo = ResourceRepository(db)

    if subject not in context.ids:
        raise KeyError(f"找不到科目 '{subject}' 的 ID")

    subject_id = uuid.UUID(context.ids[subject])

    # 確保 seed user 存在（若不存在則建立）
    from app.models.user import User
    seed_user = db.query(User).filter_by(id=SEED_USER_ID).first()
    if not seed_user:
        seed_user = User(
            id=SEED_USER_ID,
            email="seed@system.internal",
            password_hash="unused",
            display_name="Seed User",
            is_verified=True,
        )
        db.add(seed_user)
        db.flush()

    resource = Resource(
        user_id=SEED_USER_ID,
        subject_id=subject_id,
        name=resource_name,
        type="pdf",
        status=ResourceStatus.COMPLETED,
    )
    repo.save(resource)
    context.ids[resource_name] = str(resource.id)
