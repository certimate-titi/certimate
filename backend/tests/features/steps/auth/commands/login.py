from behave import when


@when('使用者以 Email "{email}" 和密碼 "{password}" 進行登入')
def step_impl(context, email, password):
    response = context.api_client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    context.last_response = response
