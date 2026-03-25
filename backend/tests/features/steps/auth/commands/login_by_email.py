from behave import when


@when('使用者 "{email}" 成功登入系統')
def step_impl(context, email):
    response = context.api_client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Password1!",
        },
    )
    context.last_response = response
