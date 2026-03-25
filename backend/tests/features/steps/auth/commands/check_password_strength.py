from behave import when


@when('使用者輸入密碼 "{password}"')
def step_impl(context, password):
    response = context.api_client.post(
        "/api/v1/auth/password-strength",
        json={"password": password},
    )
    context.last_response = response
