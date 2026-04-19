"""When 使用者以 Token 重設密碼 — Command"""

from behave import given, when, then


@given('使用者 "{email}" 已取得有效的密碼重設 Token')
def step_impl_obtain_reset_token(context, email):
    """為測試直接產生有效的重設 Token（模擬使用者點擊郵件連結後取得）。"""
    from app.services.auth_service import _generate_reset_token

    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"
    context.memo["reset_token"] = _generate_reset_token(str(user_id))


@when('使用者以該 Token 將密碼重設為 "{password}"')
def step_impl_reset_with_memo_token(context, password):
    token = context.memo.get("reset_token")
    assert token, "context.memo['reset_token'] 未設定"
    response = context.api_client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": password},
    )
    context.last_response = response


@when('使用者以無效 Token "{token}" 將密碼重設為 "{password}"')
def step_impl_reset_with_invalid_token(context, token, password):
    response = context.api_client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": password},
    )
    context.last_response = response


@then('使用者應能以新密碼 "{password}" 成功登入')
def step_impl_login_with_new_password(context, password):
    email = context.memo.get("last_action_email")
    if not email:
        for k, v in context.ids.items():
            if "@" in k:
                email = k
                break
    assert email, "無法從 context 推斷登入 email"
    response = context.api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, \
        f"以新密碼登入失敗: {response.status_code} {response.text}"
