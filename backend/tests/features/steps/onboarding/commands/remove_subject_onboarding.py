"""When 使用者移除科目（Onboarding 中）— Command (DELETE)"""

from behave import when


@when('使用者移除 "{subject}"')
def step_impl(context, subject):
    token = context.memo.get("current_token")
    subject_id = context.ids.get(f"subject_{subject}", subject)

    response = context.api_client.delete(
        f"/api/v1/onboarding/subjects/{subject_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
