"""B2C 散客用戶已登入，JWT 不含 tenant_id."""

import uuid
from behave import given
from app.models.user import User
from app.core.config import PUBLIC_B2C_TENANT_ID


@given("B2C 散客用戶已登入，JWT 不含 tenant_id")
def step_impl(context):
    """建立 B2C 散客用戶，並生成不含 tenant_id 的 JWT。"""
    user_id = uuid.uuid4()
    from app.models.user import UserStatus
    user = User(
        id=user_id,
        email="b2c_guest@test.example.com",
        password_hash="$2b$12$test_hash_placeholder",
        status=UserStatus.ACTIVE,
        subscription_plan="FREE",
    )
    context.db_session.merge(user)
    context.db_session.commit()

    # 生成不含 tenant_id 的 JWT（B2C 散客）— 系統會自動 fallback 到 public_b2c
    token = context.jwt_helper.generate_token(str(user_id))
    context.memo["current_token"] = token
    context.memo["current_user_id"] = str(user_id)
    context.ids["b2c_guest"] = str(user_id)
    # 讓 Then 步驟可以查詢 public_b2c 的 UUID
    context.ids["public_b2c"] = PUBLIC_B2C_TENANT_ID
