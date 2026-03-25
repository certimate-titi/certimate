from behave import given
from app.repositories.user_repository import UserRepository


@given('使用者 "{email}" 原本為 Email/密碼註冊方式')
def step_impl(context, email):
    repo = UserRepository(context.db_session)
    user = repo.find_by_email(email)
    assert user is not None, f"找不到使用者 '{email}'，請先在 Background 建立"
    assert user.auth_provider == "email", \
        f"使用者 '{email}' 的 auth_provider 應為 'email'，實際為 '{user.auth_provider}'"
