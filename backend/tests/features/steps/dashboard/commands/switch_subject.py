"""When 使用者切換科目 — Command (GET with subject param)"""

from behave import when


@when('使用者 "{email}" 切換至 "{subject_name}"')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token}"},
        params={"subject": subject_name},
    )
    context.last_response = response
