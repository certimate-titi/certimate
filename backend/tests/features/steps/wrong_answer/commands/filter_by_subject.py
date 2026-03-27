"""When 使用者在錯題複習頁面選擇科目 — Command (GET)"""

import uuid

from behave import when


@when('使用者 "{email}" 在錯題複習頁面選擇科目 "{subject_name}"')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_key = f"subject_{subject_name}"
    subject_id = context.ids.get(subject_key, "")

    response = context.api_client.get(
        f"/api/v1/wrong-answers?subject_id={subject_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
