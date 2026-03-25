from behave import given
from app.repositories.user_repository import UserRepository


@given('使用者 "{email}" 已建立至少一個備考科目的學習歷程')
def step_impl(context, email):
    repo = UserRepository(context.db_session)
    user = repo.find_by_email(email)
    assert user is not None, f"找不到使用者 '{email}'，請先在 Background 建立"

    # 標記使用者已完成 onboarding（代表已有學習歷程）
    user.onboarding_completed = True
    context.db_session.commit()
