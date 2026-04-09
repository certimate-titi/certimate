"""一個不含 tenant_id 的舊格式 JWT（只有 sub 欄位）."""

import uuid
from behave import given
from app.models.user import User


@given("一個不含 tenant_id 的舊格式 JWT（只有 sub 欄位）")
def step_impl(context):
    """建立 B2C 用戶，並生成舊格式 JWT（不含 tenant_id）。"""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="legacy_user@test.example.com",
        password_hash="$2b$12$test_hash_placeholder",
        is_verified=True,
        subscription_tier="FREE",
    )
    context.db_session.merge(user)
    context.db_session.commit()

    # 只含 sub 的舊格式 JWT
    token = context.jwt_helper.generate_token(str(user_id))
    context.memo["legacy_token"] = token
    context.memo["current_token"] = token
    context.ids["legacy_user"] = str(user_id)
