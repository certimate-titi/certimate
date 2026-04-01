from behave import when


@when('使用者以無效驗證 token 確認 Email')
def step_impl(context):
    response = context.api_client.post(
        "/api/v1/auth/verify-email",
        json={"token": "invalid-token-abc123"},
    )
    context.last_response = response
