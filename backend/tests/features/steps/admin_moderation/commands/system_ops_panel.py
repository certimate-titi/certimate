"""When 系統維運面板快速操作 — Command"""

from behave import when


@when('使用者 "{email}" 於系統維運面板點擊「重設 AI 速率限制」按鈕')
def step_impl_reset_ai_limits(context, email):
    """呼叫 API 觸發重設 AI 速率限制確認流程。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/admin/system/reset-ai-limits/confirm",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["pending_system_action"] = "reset-ai-limits"
    context.memo["admin_token"] = token


@when('使用者 "{email}" 於系統維運面板點擊「清除系統快取」按鈕')
def step_impl_clear_cache(context, email):
    """呼叫 API 觸發清除系統快取確認流程。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/admin/system/clear-cache/confirm",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["pending_system_action"] = "clear-cache"
    context.memo["admin_token"] = token
