"""When 重新寄送驗證信 UI — 模擬點擊後呼叫 /auth/resend-verification 並啟動 60 秒冷卻。"""

from behave import when


@when('使用者點擊「重新寄送驗證信」按鈕')
def step_impl_click_resend_verification(context):
    email = context.memo.get("pending_verification_email", "pending@example.com")
    response = context.api_client.post(
        "/api/v1/auth/resend-verification",
        json={"email": email},
    )
    context.last_response = response
    context.memo["resend_cooldown_remaining"] = 60
    context.memo["resend_cooldown_ended"] = False
