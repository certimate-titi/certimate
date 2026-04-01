from behave import when


@when('使用者透過 Google SSO 登入且 Email 為 "{email}"')
def step_impl(context, email):
    response = context.api_client.post(
        "/api/v1/auth/google-sso",
        json={
            "email": email,
            "google_id_token": "mock-google-token",
        },
    )
    context.last_response = response
