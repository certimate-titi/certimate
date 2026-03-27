"""When 使用者設定以下偏好 — Command (POST)"""

from behave import when


@when('使用者設定以下偏好：')
def step_impl(context):
    token = context.memo.get("current_token")

    prefs = {}
    for row in context.table:
        field = row["欄位"]
        value = row["值"]
        if field == "每日學習時間":
            prefs["daily_study_minutes"] = int(value.replace(" 分鐘", ""))
        elif field == "偏好學習方式":
            prefs["learning_preference"] = value

    response = context.api_client.post(
        "/api/v1/onboarding/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json=prefs,
    )
    context.last_response = response
