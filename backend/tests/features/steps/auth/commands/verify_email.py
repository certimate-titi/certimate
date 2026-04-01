from behave import when
from app.services.auth_service import _generate_verification_token
from app.repositories.user_repository import UserRepository


@when('使用者以有效驗證 token 確認 Email')
def step_impl(context):
    # 取得最近操作的使用者 email
    email = context.memo.get("last_email")
    assert email is not None, "找不到最近操作的使用者 email，請先在 Given 中設定"

    # 從 DB 查找使用者以取得 ID
    repo = UserRepository(context.db_session)
    user = repo.find_by_email(email)
    assert user is not None, f"找不到 email='{email}' 的使用者"

    # 生成有效的驗證 token
    token = _generate_verification_token(str(user.id))

    response = context.api_client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )
    context.last_response = response
    context.memo["last_email"] = email
