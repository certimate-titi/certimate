from behave import when


@when('使用者以 Email "{email}" 請求重寄驗證信')
def step_impl(context, email):
    response = context.api_client.post(
        "/api/v1/auth/resend-verification",
        json={"email": email},
    )
    context.last_response = response
