from behave import then
from app.repositories.user_repository import UserRepository


STATUS_MAP = {
    "已啟用": "active",
    "待驗證": "pending",
    "已停用": "suspended",
    "冷卻中": "cooling",
    "已刪除": "deleted",
}


@then('該帳號狀態應更新為 "{status}"')
def step_impl(context, status):
    email = context.memo.get("last_email")
    assert email is not None, "找不到最近操作的使用者 email"

    repo = UserRepository(context.db_session)
    context.db_session.expire_all()
    user = repo.find_by_email(email)
    assert user is not None, f"DB 中找不到 email='{email}' 的使用者"

    expected_status = STATUS_MAP.get(status, status)
    actual_status = user.status.value if hasattr(user.status, "value") else user.status
    assert actual_status == expected_status, \
        f"帳號狀態應為 '{expected_status}'，實際為 '{actual_status}'"
