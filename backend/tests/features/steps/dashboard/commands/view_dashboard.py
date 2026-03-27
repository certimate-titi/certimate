"""When 使用者查看儀表板 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看儀表板')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查看儀表板，科目為 "{subject_name}"')
def step_impl_with_subject(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token}"},
        params={"subject": subject_name},
    )
    context.last_response = response
