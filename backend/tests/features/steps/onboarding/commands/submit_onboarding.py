"""When 使用者提交 Onboarding 設定 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 提交 Onboarding 設定：')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subjects = []
    for row in context.table:
        subjects.append({
            "subject_name": row["備考科目"],
            "exam_date": row["考試日期"],
            "self_assessed_level": row["自評程度"],
        })

    display_name = context.table[0]["顯示名稱"] if context.table else None
    daily_minutes = int(context.table[0]["每日學習時間"]) if context.table else 30
    preference = context.table[0]["偏好學習方式"] if context.table else "mixed"

    response = context.api_client.post(
        "/api/v1/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": display_name,
            "subjects": subjects,
            "daily_study_minutes": daily_minutes,
            "learning_preference": preference,
        },
    )
    context.last_response = response


@when('使用者 "{email}" 提交空的 Onboarding 設定')
def step_impl_empty(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"subjects": [], "daily_study_minutes": 30, "learning_preference": "mixed"},
    )
    context.last_response = response
