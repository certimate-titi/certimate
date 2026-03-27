"""When 使用者選擇自訂並輸入每日學習時間 — Command (POST)"""

from behave import when


@when('使用者選擇「自訂」並輸入每日學習時間為 {minutes:d} 分鐘')
def step_impl(context, minutes):
    token = context.memo.get("current_token")

    response = context.api_client.post(
        "/api/v1/onboarding/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"daily_study_minutes": minutes, "learning_preference": "custom"},
    )
    context.last_response = response
