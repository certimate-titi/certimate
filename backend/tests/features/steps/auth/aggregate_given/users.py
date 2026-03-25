from behave import given
from app.models.user import User, UserStatus, UserRole, SubscriptionPlan
from app.repositories.user_repository import UserRepository


STATUS_MAP = {
    "已啟用": UserStatus.ACTIVE,
    "待驗證": UserStatus.PENDING,
    "已停用": UserStatus.SUSPENDED,
    "冷卻中": UserStatus.COOLING,
    "已刪除": UserStatus.DELETED,
}

ROLE_MAP = {
    "USER": UserRole.USER,
    "ADMIN": UserRole.ADMIN,
    "ORG_ADMIN": UserRole.ORG_ADMIN,
    "SUPER_ADMIN": UserRole.SUPER_ADMIN,
}

PLAN_MAP = {
    "FREE": SubscriptionPlan.FREE,
    "PRO_199": SubscriptionPlan.PRO_199,
    "PRO_PLUS_399": SubscriptionPlan.PRO_PLUS_399,
    "ULTRA_399": SubscriptionPlan.PRO_PLUS_399,
    "ULTRA_1599": SubscriptionPlan.ULTRA_1599,
}

AUTH_PROVIDER_MAP = {
    "email": "email",
    "google": "google",
}


@given('系統中有以下使用者帳號：')
def step_impl(context):
    repo = UserRepository(context.db_session)

    for row in context.table:
        user = User(
            email=row["Email"],
            auth_provider=AUTH_PROVIDER_MAP.get(row["驗證方式"], row["驗證方式"]),
            subscription_plan=PLAN_MAP.get(row["訂閱方案"], SubscriptionPlan.FREE),
            role=ROLE_MAP.get(row["角色"], UserRole.USER),
            status=STATUS_MAP.get(row["狀態"], UserStatus.ACTIVE),
            password_hash="$2b$12$hashed_test_password",
            agreed_to_terms=True,
        )
        saved_user = repo.save(user)
        context.ids[row["Email"]] = str(saved_user.id)
        context.ids[row["使用者 ID"]] = str(saved_user.id)
