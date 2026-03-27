"""When 使用者新增備考科目 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 新增備考科目 "{subject_name}"，考試日期為 "{exam_date}"，自評程度為 "{level}"')
def step_impl(context, email, subject_name, exam_date, level):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/onboarding/subjects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject_name": subject_name,
            "exam_date": exam_date,
            "self_assessed_level": level,
        },
    )
    context.last_response = response
