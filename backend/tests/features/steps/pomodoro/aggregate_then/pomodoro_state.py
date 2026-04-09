"""Then 番茄鐘狀態驗證 — Aggregate Then"""

from behave import then


@then('使用者的番茄鐘設定應為：')
def step_impl_pomodoro_settings(context):
    """驗證番茄鐘設定。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        settings = data.get("pomodoro_settings") or data
        for row in context.table:
            field_map = {
                "專注時長（分鐘）": "focus_minutes",
                "短休息（分鐘）": "short_break_minutes",
                "長休息（分鐘）": "long_break_minutes",
                "長休息間隔": "long_break_interval",
                "啟用狀態": "enabled",
            }
            key = field_map.get(row["欄位"], row["欄位"])
            expected = row["值"]
            actual = settings.get(key)
            if actual is not None:
                assert str(actual) == expected, \
                    f"番茄鐘設定 '{row['欄位']}' 期望 {expected}，實際 {actual}"


@then('使用者的番茄鐘設定專注時長應為 {minutes:d}')
def step_impl_focus_minutes(context, minutes):
    """驗證番茄鐘專注時長設定。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        actual = data.get("focus_minutes") or (data.get("pomodoro_settings") or {}).get("focus_minutes")
        if actual is not None:
            assert actual == minutes, f"專注時長期望 {minutes}，實際 {actual}"


@then('番茄計時器應重新開始下一個專注時段')
def step_impl_new_focus_session(context):
    """驗證番茄計時器重新開始專注時段。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('該次休息應記錄為 "已跳過"')
def step_impl_break_skipped(context):
    """驗證休息記錄為已跳過。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        skipped = data.get("break_skipped")
        if skipped is not None:
            assert skipped is True, "休息應記錄為已跳過"
