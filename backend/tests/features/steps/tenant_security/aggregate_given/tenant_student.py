"""每個租戶各有 1 名學生用戶."""

import uuid
from behave import given
from app.models.user import User
from app.repositories.user_repository import UserRepository


@given("每個租戶各有 1 名學生用戶")
def step_impl(context):
    """為每個已建立的租戶各建立一個學生用戶。"""
    user_repo = UserRepository(context.db_session)

    for slug, tenant_id in [(k, v) for k, v in context.ids.items() if not k.startswith("user_")]:
        email = f"student_{slug}@test.example.com"
        user_id = uuid.uuid4()

        # 建立用戶並關聯租戶
        user = User(
            id=user_id,
            email=email,
            password_hash="$2b$12$test_hash_placeholder",
            is_verified=True,
            subscription_tier="FREE",
        )
        context.db_session.merge(user)
        context.db_session.commit()

        # 儲存 user_id，以 slug 為 key
        context.ids[f"user_{slug}"] = str(user_id)
        context.memo[f"tenant_id_{slug}"] = tenant_id
