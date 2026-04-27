"""Given 使用者已完成引導流程 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 已完成引導流程')
def step_impl(context, email):
    """標記使用者已完成引導流程。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if user and not user.onboarding_completed:
        user.onboarding_completed = True
        context.db_session.commit()
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 的密碼為 "{password}"')
def step_impl_set_password(context, email, password):
    """設定使用者密碼（測試 fixture）。"""
    from app.models.user import User
    from app.services.auth_service import _hash_password
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    user.password_hash = _hash_password(password)
    context.db_session.commit()
