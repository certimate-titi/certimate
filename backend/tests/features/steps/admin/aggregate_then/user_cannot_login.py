"""Then 使用者 X 應無法登入系統 — Aggregate Then"""

from behave import then

from app.models.user import User, UserStatus


@then('使用者 "{email}" 應無法登入系統')
def step_impl(context, email):
    db = context.db_session
    user_id = context.ids[email]

    import uuid
    user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    db.refresh(user)
    status = user.status.value if hasattr(user.status, "value") else str(user.status)
    assert status == "suspended", \
        f"預期使用者 {email} 狀態為 suspended，實際 '{status}'"
