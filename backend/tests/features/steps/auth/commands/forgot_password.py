from behave import when


@when('使用者以 Email "{email}" 申請密碼重設')
def step_impl(context, email):
    response = context.api_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": email},
    )
    context.last_response = response
