"""When 系統維運面板快速操作 — Command"""

from behave import when


def _fake_confirm_response():
    return type(
        "FakeResp", (), {
            "status_code": 200,
            "json": lambda self: {"confirm_required": True},
            "text": "confirm dialog",
        },
    )()


@when('使用者 "{email}" 於系統維運面板點擊「重設 AI 速率限制」按鈕')
def step_impl_reset_ai_limits(context, email):
    """記錄待執行動作，待後續「確認」按鈕呼叫實際 API。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.last_response = _fake_confirm_response()
    context.memo["pending_system_action"] = "reset-ai-limits"
    context.memo["admin_token"] = token


@when('使用者 "{email}" 於系統維運面板點擊「清除系統快取」按鈕')
def step_impl_clear_cache(context, email):
    """記錄待執行動作，待後續「確認」按鈕呼叫實際 API。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.last_response = _fake_confirm_response()
    context.memo["pending_system_action"] = "clear-cache"
    context.memo["admin_token"] = token
