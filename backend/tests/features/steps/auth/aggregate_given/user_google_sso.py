from behave import given
from app.models.user import User, UserStatus, SubscriptionPlan
from app.repositories.user_repository import UserRepository
from app.services.auth_service import _hash_password


STATUS_MAP = {
    "已啟用": UserStatus.ACTIVE,
    "待驗證": UserStatus.PENDING,
}


@given('使用者 "{email}" 已有 Google SSO 帳號且狀態為 "{status}"')
def step_impl(context, email, status):
    repo = UserRepository(context.db_session)
    user = repo.find_by_email(email)

    if user is None:
        user = User(
            email=email,
            auth_provider="google",
            password_hash=None,
            subscription_plan=SubscriptionPlan.FREE,
            status=STATUS_MAP.get(status, UserStatus.ACTIVE),
            agreed_to_terms=True,
        )
        user = repo.save(user)
        context.ids[email] = str(user.id)
    else:
        user.auth_provider = "google"
        user.status = STATUS_MAP.get(status, UserStatus.ACTIVE)
        context.db_session.commit()

    context.memo["last_email"] = email
