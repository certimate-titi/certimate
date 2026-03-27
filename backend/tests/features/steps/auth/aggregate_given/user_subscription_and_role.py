from behave import given
from app.models.user import SubscriptionPlan, UserRole
from app.repositories.user_repository import UserRepository


PLAN_MAP = {
    "FREE": SubscriptionPlan.FREE,
    "PRO": SubscriptionPlan.PRO,
    "PRO_PLUS": SubscriptionPlan.PRO_PLUS,
    "ULTRA": SubscriptionPlan.ULTRA,
}

ROLE_MAP = {
    "USER": UserRole.USER,
    "ADMIN": UserRole.ADMIN,
    "ORG_ADMIN": UserRole.ORG_ADMIN,
    "SUPER_ADMIN": UserRole.SUPER_ADMIN,
}


@given('使用者 "{email}" 訂閱方案為 "{plan}" 且角色為 "{role}"')
def step_impl(context, email, plan, role):
    repo = UserRepository(context.db_session)
    user = repo.find_by_email(email)
    assert user is not None, f"找不到使用者 '{email}'，請先在 Background 建立"

    user.subscription_plan = PLAN_MAP.get(plan, SubscriptionPlan.FREE)
    user.role = ROLE_MAP.get(role, UserRole.USER)
    context.db_session.commit()
