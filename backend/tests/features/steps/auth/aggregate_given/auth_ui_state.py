"""Given 身分驗證 UI 前置狀態 — Aggregate Given"""

from behave import given


@given('使用者在登入頁面的密碼欄位輸入 "{password}"')
def step_impl_login_password_input(context, password):
    """記錄登入頁密碼欄位輸入（UI 前置狀態）。"""
    context.memo["login_password_input"] = password


@given('密碼欄位目前為明文顯示模式')
def step_impl_password_visible(context):
    """記錄密碼欄位目前為明文顯示模式。"""
    context.memo["password_field_mode"] = "plaintext"


@given('使用者在註冊頁面的密碼欄位輸入 "{password}"')
def step_impl_register_password_input(context, password):
    """記錄註冊頁密碼欄位輸入（UI 前置狀態）。"""
    context.memo["register_password_input"] = password


@given('使用者已開啟服務條款彈窗')
def step_impl_terms_dialog_open(context):
    """記錄服務條款彈窗已開啟狀態。"""
    context.memo["terms_dialog_open"] = True


@given('使用者已開啟隱私權政策彈窗')
def step_impl_privacy_dialog_open(context):
    """記錄隱私權政策彈窗已開啟狀態。"""
    context.memo["privacy_dialog_open"] = True


@given('使用者在忘記密碼頁面已輸入 "{email}"')
def step_impl_forgot_password_email_input(context, email):
    """記錄忘記密碼頁面已輸入 Email。"""
    context.memo["forgot_password_email"] = email


@given('使用者已完成註冊並進入驗證信寄出頁面')
def step_impl_registration_complete_verify_page(context):
    """記錄使用者已完成註冊並進入驗證信寄出頁面。"""
    context.memo["on_verify_email_page"] = True


@given('使用者已點擊「重新寄送驗證信」且冷卻倒數已結束')
def step_impl_resend_cooldown_ended(context):
    """記錄重寄驗證信冷卻倒數已結束狀態。"""
    context.memo["resend_cooldown_ended"] = True
