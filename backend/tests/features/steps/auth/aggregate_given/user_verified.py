from behave import given
from app.models.user import User, UserStatus
from app.repositories.user_repository import UserRepository
from app.services.auth_service import _hash_password


@given('使用者 "{email}" 已完成註冊驗證')
def step_impl(context, email):
    repo = UserRepository(context.db_session)

    # 如果使用者不存在（例如 newuser），先建立
    user = repo.find_by_email(email)
    if user is None:
        user = User(
            email=email,
            auth_provider="email",
            password_hash=_hash_password("CertiMate#2024"),
            status=UserStatus.ACTIVE,
            agreed_to_terms=True,
        )
        user = repo.save(user)
        context.ids[email] = str(user.id)
    else:
        user.status = UserStatus.ACTIVE
        context.db_session.commit()
