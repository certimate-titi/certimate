"""When 使用者封存備考科目 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 封存備考科目 "{subject_name}"')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subj_key = f"subject_{subject_name}"
    subject_id = context.ids.get(subj_key, "")

    response = context.api_client.post(
        f"/api/v1/onboarding/subjects/{subject_id}/archive",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
