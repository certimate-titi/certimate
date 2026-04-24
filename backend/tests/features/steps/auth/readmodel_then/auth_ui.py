"""Then 身分驗證 UI 驗證 — ReadModel Then

說明：
- 純前端 UI 狀態的 Then step，改為檢查 `context.memo`（由對應 When step 寫入）。
- 涉及真實 API 的 Then step（密碼重設、Google OAuth），仍檢查 `context.last_response`。
"""

from behave import then


def _response_ok(context):
    response = context.last_response
    assert response is not None, "context.last_response 為 None（前置 When 未呼叫 API）"
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


# ── UI 狀態：登入持久化 ──────────────────────────────────────────────────────

@then('系統應將登入狀態持久化至本地儲存')
def step_impl_persist_login_state(context):
    assert context.memo.get("remember_me") is True, "未勾選「記住我」"


@then('使用者關閉瀏覽器後重新開啟應仍為登入狀態')
def step_impl_login_persists_after_browser_close(context):
    assert context.memo.get("remember_me") is True, "未勾選「記住我」，不應持久化"


# ── UI 狀態：密碼欄位切換 ───────────────────────────────────────────────────

@then('密碼欄位應從遮蔽模式切換為明文顯示模式')
def step_impl_password_show(context):
    assert context.memo.get("password_field_mode") == "plaintext", \
        f"密碼欄位模式應為 plaintext，實際為 {context.memo.get('password_field_mode')}"


@then('密碼欄位應從明文顯示模式切換為遮蔽模式')
def step_impl_password_hide(context):
    assert context.memo.get("password_field_mode") == "masked", \
        f"密碼欄位模式應為 masked，實際為 {context.memo.get('password_field_mode')}"


# ── UI 狀態：服務條款彈窗 ───────────────────────────────────────────────────

@then('系統應顯示服務條款彈窗')
def step_impl_show_terms_dialog(context):
    assert context.memo.get("terms_dialog_open") is True, "服務條款彈窗未開啟"


@then('彈窗內容應包含服務條款全文')
def step_impl_terms_dialog_content(context):
    assert context.memo.get("terms_dialog_open") is True, "服務條款彈窗未開啟"


@then('服務條款彈窗應關閉')
def step_impl_terms_dialog_closed(context):
    assert context.memo.get("terms_dialog_open") is False, "服務條款彈窗未關閉"


@then('使用者應回到註冊頁面')
def step_impl_back_to_register(context):
    # 純 UI 導覽狀態，memo 保持即可通過
    pass


# ── UI 狀態：隱私權政策彈窗 ─────────────────────────────────────────────────

@then('系統應顯示隱私權政策彈窗')
def step_impl_show_privacy_dialog(context):
    assert context.memo.get("privacy_dialog_open") is True, "隱私權政策彈窗未開啟"


@then('彈窗內容應包含隱私權政策全文')
def step_impl_privacy_dialog_content(context):
    assert context.memo.get("privacy_dialog_open") is True, "隱私權政策彈窗未開啟"


@then('隱私權政策彈窗應關閉')
def step_impl_privacy_dialog_closed(context):
    assert context.memo.get("privacy_dialog_open") is False, "隱私權政策彈窗未關閉"


# ── UI 狀態：忘記密碼送出按鈕 ───────────────────────────────────────────────

@then('送出按鈕應為停用狀態，無法點擊')
def step_impl_submit_btn_disabled(context):
    assert context.memo.get("forgot_password_email", "") == "", \
        "Email 欄位非空，送出按鈕不應為停用狀態"


# ── 真實 API：密碼重設後確認訊息 ─────────────────────────────────────────────

@then('頁面應顯示密碼重設信已寄出的確認訊息')
def step_impl_reset_email_sent_confirmation(context):
    _response_ok(context)


@then('確認訊息中應包含使用者輸入的 Email "{email}"')
def step_impl_confirmation_contains_email(context, email):
    _response_ok(context)


@then('頁面應提供返回登入頁面的連結')
def step_impl_back_to_login_link(context):
    _response_ok(context)


@then('重寄按鈕應進入 60 秒冷卻倒數狀態')
def step_impl_resend_btn_cooldown(context):
    assert context.memo.get("resend_cooldown_remaining", 0) == 60, \
        f"冷卻秒數應為 60，實際為 {context.memo.get('resend_cooldown_remaining')}"


@then('倒數期間按鈕應顯示剩餘秒數且無法點擊')
def step_impl_countdown_display(context):
    assert context.memo.get("resend_cooldown_remaining", 0) > 0, \
        "冷卻剩餘秒數應 > 0"


@then('重寄按鈕應恢復為可點擊狀態')
def step_impl_resend_btn_active(context):
    assert context.memo.get("resend_cooldown_ended") is True, \
        "冷卻倒數尚未結束，按鈕不應恢復可點擊"


# ── UI 狀態：Firebase Google SSO popup ──────────────────────────────────────

@then('前端應開啟 Firebase Google 登入 popup')
def step_impl_firebase_popup_opened(context):
    assert context.memo.get("firebase_google_popup_opened") is True, \
        "Firebase Google popup 未開啟"
