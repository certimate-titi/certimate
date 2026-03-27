"""When 使用者新增備考科目（後續管理）— Command (POST)"""

from behave import when


@when('使用者新增備考科目 "{subject}"，設定考試日期為 "{date}"，自評程度為 "{level}"')
def step_impl(context, subject, date, level):
    email = context.memo.get("current_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_id = context.ids.get(email)
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/subjects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject_name": subject,
            "exam_date": date,
            "self_assessed_level": level,
        },
    )
    context.last_response = response
