"""Given 測試 Scenario 已建立 {count} 筆 resources（tenant_id = test_tenant）."""

import uuid
from behave import given
from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope
from app.models.subject import Subject


@given('測試 Scenario 已建立 {count:d} 筆 resources（tenant_id = test_tenant）')
def step_impl(context, count):
    """建立指定數量的 resources，使用測試 tenant_id。"""
    test_tenant_id = uuid.uuid4()
    context.test_tenant_id = str(test_tenant_id)
    context.memo["test_tenant_id"] = str(test_tenant_id)

    # 需要一個 subject 和 user
    import uuid as _uuid
    from app.models.user import User

    user_id = _uuid.uuid4()
    from app.models.user import UserStatus
    user = User(
        id=user_id,
        email=f"test_tenant_user_{user_id.hex[:8]}@test.example.com",
        password_hash="$2b$12$test_hash",
        status=UserStatus.ACTIVE,
        subscription_plan="FREE",
    )
    context.db_session.merge(user)

    from app.models.subject import SubjectCategory
    category = context.db_session.query(SubjectCategory).first()
    if category is None:
        category = SubjectCategory(name="Test Category")
        context.db_session.add(category)
        context.db_session.commit()
        context.db_session.refresh(category)
    subject = Subject(id=_uuid.uuid4(), name="Test Subject", category_id=category.id)
    context.db_session.merge(subject)
    context.db_session.commit()

    for i in range(count):
        resource = Resource(
            id=_uuid.uuid4(),
            user_id=user_id,
            subject_id=subject.id,
            name=f"Test Resource {i}",
            type=ResourceType.PDF,
            scope=ResourceScope.PERSONAL,
            status=ResourceStatus.COMPLETED,
            tenant_id=test_tenant_id,
        )
        context.db_session.add(resource)
    context.db_session.commit()
