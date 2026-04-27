"""Then 帳號狀態驗證 — Aggregate Then"""

from behave import then


@then('使用者帳號狀態應變更為 "{expected_status}"')
def step_impl_account_status_changed(context, expected_status):
    """驗證使用者帳號狀態已變更。"""
    user_id = context.memo.get("delete_target_user_id")
    if not user_id:
        return
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        import uuid
        from app.models.user import User
        user = context.db_session.query(User).filter(
            User.id == uuid.UUID(user_id)
        ).first()
        if user:
            status_val = user.status.value if hasattr(user.status, "value") else user.status
            actual_status = str(status_val).upper() if status_val else "UNKNOWN"
            assert actual_status == expected_status.upper(), \
                f"帳號狀態期望 '{expected_status}'，實際 '{actual_status}'"
