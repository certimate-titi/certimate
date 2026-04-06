"""When 管理員對考科執行增量逆向工程 — Command (POST)"""

from behave import when


@when('管理員 "{email}" 對考科 "{subject_name}" 執行增量逆向工程')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = context.ids.get(f"subject_name_{subject_name}")
    if not subject_id:
        raise KeyError(f"找不到考科 '{subject_name}'")

    response = context.api_client.post(
        f"/api/v1/reverse-engineering/subjects/{subject_id}/incremental",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
