"""B2C 散客用戶已登入，JWT 不含 tenant_id."""

import uuid
from behave import given
from app.models.user import User


@given("B2C 散客用戶已登入，JWT 不含 tenant_id")
def step_impl(context):
    """建立 B2C 散客用戶，並生成不含 tenant_id 的 JWT。"""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="b2c_guest@test.example.com",
        password_hash="$2b$12$test_hash_placeholder",
        is_verified=True,
        subscription_tier="FREE",
    )
    context.db_session.merge(user)
    context.db_session.commit()

    # 生成不含 tenant_id 的 JWT（B2C 散客）
    token = context.jwt_helper.generate_token(str(user_id))
    context.memo["current_token"] = token
    context.memo["current_user_id"] = str(user_id)
    context.ids["b2c_guest"] = str(user_id)
