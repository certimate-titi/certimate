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
