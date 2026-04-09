"""已登入的用戶（一般用戶，用於 SSRF 測試）."""

import uuid
from behave import given
from app.models.user import User


@given("已登入的用戶")
def step_impl(context):
    """建立並登入一個一般用戶。"""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"ssrf_test_{user_id.hex[:8]}@test.example.com",
        password_hash="$2b$12$test_hash_placeholder",
        is_verified=True,
        subscription_tier="FREE",
    )
    context.db_session.merge(user)
    context.db_session.commit()

    token = context.jwt_helper.generate_token(str(user_id))
    context.memo["current_token"] = token
    context.ids["current_user"] = str(user_id)
