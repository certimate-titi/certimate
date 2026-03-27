"""When 使用者點擊開始我的學習旅程 — Command (POST)"""

from behave import when


@when('使用者點擊「開始我的學習旅程」')
def step_impl(context):
    token = context.memo.get("current_token")

    # Build subjects list from memo if available (from Step 1-3 settings)
    subjects_str = context.memo.get("onboarding_subjects", "")
    subjects = []
    if subjects_str:
        for name in subjects_str.split(", "):
            subjects.append({
                "subject_name": name.strip(),
                "exam_date": None,
                "self_assessed_level": "beginner",
            })

    body = {
        "subjects": subjects,
        "daily_study_minutes": int(context.memo.get("onboarding_daily_minutes", "30").replace(" 分鐘", "")),
        "learning_preference": context.memo.get("onboarding_preference", "mixed"),
    }
    display_name = context.memo.get("onboarding_display_name")
    if display_name:
        body["display_name"] = display_name

    response = context.api_client.post(
        "/api/v1/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    context.last_response = response
