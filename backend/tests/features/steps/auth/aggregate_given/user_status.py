from behave import given
from app.models.user import UserStatus
from app.repositories.user_repository import UserRepository


STATUS_MAP = {
    "已啟用": UserStatus.ACTIVE,
    "待驗證": UserStatus.PENDING,
    "已停用": UserStatus.SUSPENDED,
    "冷卻中": UserStatus.COOLING,
    "已刪除": UserStatus.DELETED,
}


@given('使用者 "{email}" 帳號狀態為 "{status}"')
def step_impl(context, email, status):
    repo = UserRepository(context.db_session)
    user = repo.find_by_email(email)
    assert user is not None, f"找不到 email='{email}' 的使用者，請先在 Background 中建立"

    user.status = STATUS_MAP.get(status, status)
    context.db_session.commit()
    context.memo["last_email"] = email
