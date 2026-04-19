"""When 身分驗證 UI 互動操作 — Command"""

from behave import when


@when('使用者在登入頁面勾選「記住我」')
def step_impl_check_remember_me(context):
    """記錄勾選「記住我」狀態（純前端 UI，不呼叫 API）。"""
    context.memo["remember_me"] = True


@when('使用者點擊密碼欄位的顯示/隱藏切換按鈕')
def step_impl_toggle_password_visibility(context):
    """切換密碼欄位顯示/隱藏（純前端 UI，不呼叫 API）。"""
    current_mode = context.memo.get("password_field_mode", "masked")
    context.memo["password_field_mode"] = (
        "plaintext" if current_mode == "masked" else "masked"
    )


@when('使用者在註冊頁面輸入密碼 "{password}"')
def step_impl_register_input_password(context, password):
    """呼叫 API 驗證密碼強度（在 Red 階段可能返回 404）。"""
    response = context.api_client.post(
        "/api/v1/auth/check-password-strength",
        json={"password": password},
    )
    context.last_response = response
    context.memo["register_password_input"] = password


@when('使用者在註冊頁面點擊「服務條款」連結')
def step_impl_click_terms_link(context):
    """觸發服務條款彈窗顯示（純前端 UI，不呼叫 API）。"""
    context.memo["terms_dialog_open"] = True


@when('使用者點擊彈窗的關閉按鈕')
def step_impl_close_dialog(context):
    """關閉彈窗（純前端 UI，不呼叫 API）。"""
    context.memo["terms_dialog_open"] = False
    context.memo["privacy_dialog_open"] = False


@when('使用者在註冊頁面點擊「隱私權政策」連結')
def step_impl_click_privacy_link(context):
    """觸發隱私權政策彈窗顯示（純前端 UI，不呼叫 API）。"""
    context.memo["privacy_dialog_open"] = True


@when('使用者在忘記密碼頁面未輸入任何 Email')
def step_impl_forgot_password_no_email(context):
    """模擬忘記密碼頁面無 Email 輸入狀態（純前端 UI，不呼叫 API）。"""
    context.memo["forgot_password_email"] = ""


@when('使用者清空 Email 欄位')
def step_impl_clear_email_field(context):
    """清空 Email 欄位（純前端 UI，不呼叫 API）。"""
    context.memo["forgot_password_email"] = ""


@when('使用者在登入頁面點擊「以 Google 帳號登入」按鈕')
def step_impl_click_google_login(context):
    """呼叫 API 取得 Google OAuth 授權 URL。"""
    response = context.api_client.get("/api/v1/auth/google/oauth-url")
    context.last_response = response


@when('使用者完成 Google OAuth 授權且 Email 為 "{email}"')
def step_impl_complete_google_oauth(context, email):
    """呼叫 API 完成 Google OAuth 授權登入。"""
    response = context.api_client.post(
        "/api/v1/auth/google/callback",
        json={"email": email, "google_token": "mock_token"},
    )
    context.last_response = response
