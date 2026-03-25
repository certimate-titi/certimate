from behave import when


@when('使用者以 Email "{email}" 和密碼 "{password}" 進行註冊')
def step_impl(context, email, password):
    response = context.api_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "agreed_to_terms": True,
        },
    )
    context.last_response = response
