"""When 系統嘗試為使用者的科目初始化排程 — Command (POST)"""

from behave import when


@when('系統嘗試為使用者 "{email}" 的 {subject_name} 科目初始化排程')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subj_key = f"subject_{subject_name}"
    subject_id = context.ids.get(subj_key, "")

    response = context.api_client.post(
        "/api/v1/schedule/init",
        headers={"Authorization": f"Bearer {token}"},
        json={"subject_id": subject_id},
    )
    context.last_response = response
