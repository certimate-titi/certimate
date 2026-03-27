"""When 系統為使用者的科目計算學習模式 — Command (POST)"""

from behave import when


@when('系統為使用者 "{email}" 的 {subject_name} 科目計算學習模式')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subj_key = f"subject_{subject_name}"
    subject_id = context.ids.get(subj_key, "")

    today = context.memo.get("today")
    body = {"subject_id": subject_id}
    if today:
        body["today"] = today.isoformat()

    response = context.api_client.post(
        "/api/v1/schedule/calculate-mode",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    context.last_response = response
