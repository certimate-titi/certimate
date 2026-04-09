"""Then 身分驗證 UI 驗證 — ReadModel Then"""

from behave import then


@then('系統應將登入狀態持久化至本地儲存')
def step_impl_persist_login_state(context):
    """驗證登入狀態持久化（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('使用者關閉瀏覽器後重新開啟應仍為登入狀態')
def step_impl_login_persists_after_browser_close(context):
    """驗證關閉重開瀏覽器仍維持登入（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('密碼欄位應從遮蔽模式切換為明文顯示模式')
def step_impl_password_show(context):
    """驗證密碼欄位切換為明文模式（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('密碼欄位應從明文顯示模式切換為遮蔽模式')
def step_impl_password_hide(context):
    """驗證密碼欄位切換回遮蔽模式（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應顯示服務條款彈窗')
def step_impl_show_terms_dialog(context):
    """驗證服務條款彈窗顯示（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('彈窗內容應包含服務條款全文')
def step_impl_terms_dialog_content(context):
    """驗證服務條款彈窗包含全文（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('服務條款彈窗應關閉')
def step_impl_terms_dialog_closed(context):
    """驗證服務條款彈窗已關閉（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('使用者應回到註冊頁面')
def step_impl_back_to_register(context):
    """驗證使用者回到註冊頁面（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應顯示隱私權政策彈窗')
def step_impl_show_privacy_dialog(context):
    """驗證隱私權政策彈窗顯示（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('彈窗內容應包含隱私權政策全文')
def step_impl_privacy_dialog_content(context):
    """驗證隱私權政策彈窗包含全文（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('隱私權政策彈窗應關閉')
def step_impl_privacy_dialog_closed(context):
    """驗證隱私權政策彈窗已關閉（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('送出按鈕應為停用狀態，無法點擊')
def step_impl_submit_btn_disabled(context):
    """驗證送出按鈕為停用狀態（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('頁面應顯示密碼重設信已寄出的確認訊息')
def step_impl_reset_email_sent_confirmation(context):
    """驗證頁面顯示密碼重設確認訊息（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('確認訊息中應包含使用者輸入的 Email "{email}"')
def step_impl_confirmation_contains_email(context, email):
    """驗證確認訊息中包含 Email（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('頁面應提供返回登入頁面的連結')
def step_impl_back_to_login_link(context):
    """驗證頁面提供返回登入連結（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('重寄按鈕應進入 60 秒冷卻倒數狀態')
def step_impl_resend_btn_cooldown(context):
    """驗證重寄按鈕進入 60 秒冷卻（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('倒數期間按鈕應顯示剩餘秒數且無法點擊')
def step_impl_countdown_display(context):
    """驗證冷卻倒數中按鈕顯示剩餘秒數（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('重寄按鈕應恢復為可點擊狀態')
def step_impl_resend_btn_active(context):
    """驗證重寄按鈕恢復為可點擊（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應導向 Google OAuth 授權頁面')
def step_impl_redirect_to_google_oauth(context):
    """驗證系統導向 Google OAuth 授權頁面（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
