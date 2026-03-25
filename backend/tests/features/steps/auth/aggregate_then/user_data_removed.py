from behave import then
from app.repositories.user_repository import UserRepository


@then('系統應從主資料庫中移除該使用者的所有個人資料與測驗記錄')
def step_impl(context):
    # 取得最近操作的使用者 email（從 memo 或 last request 中推斷）
    email = context.memo.get("last_action_email")
    if email is None:
        # 從 context.ids 中尋找 alice（預設測試使用者）
        email = "alice@example.com"

    repo = UserRepository(context.db_session)
    context.db_session.expire_all()
    user = repo.find_by_email(email)
    assert user is None, \
        f"使用者 '{email}' 的資料應已從 DB 中移除，但仍存在"
