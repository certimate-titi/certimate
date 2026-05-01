from behave import given
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository


ROLE_MAP = {
    "USER": UserRole.USER,
    "user": UserRole.USER,
    "ADMIN": UserRole.ADMIN,
    "admin": UserRole.ADMIN,
    "ORG_ADMIN": UserRole.ORG_ADMIN,
    "org_admin": UserRole.ORG_ADMIN,
    "SUPER_ADMIN": UserRole.SUPER_ADMIN,
    "super_admin": UserRole.SUPER_ADMIN,
}


@given('使用者 "{email}" 角色為 "{role}"')
def step_impl(context, email, role):
    repo = UserRepository(context.db_session)
    user = repo.find_by_email(email)
    assert user is not None, f"找不到使用者 '{email}'，請先在 Background 建立"

    user.role = ROLE_MAP.get(role, UserRole.USER)
    context.db_session.commit()
