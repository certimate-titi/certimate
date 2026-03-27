"""Then 每日學習時間應設定為 N 分鐘 — ReadModel Then"""

from behave import then


@then('每日學習時間應設定為 {minutes:d} 分鐘')
def step_impl(context, minutes):
    response = context.last_response
    assert response.status_code in [200, 201], \
        f"預期成功（2XX），實際 {response.status_code}: {response.text}"
    data = response.json()
    actual = data.get("daily_study_minutes")
    assert actual == minutes, \
        f"預期每日學習時間 {minutes} 分鐘，實際 {actual}"
